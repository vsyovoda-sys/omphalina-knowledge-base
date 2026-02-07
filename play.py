#!/usr/bin/env python3
"""
Omphalina — 历史物质模拟器 · 命令行交互测试前端

用途：测试后端故事层（storylines/ + encyclopedia/）是否足够完善。
玩法：
  1. 选择一个化合物作为起点
  2. AI 给出历史背景和事件描述
  3. 每一轮给出 3-4 个选项（含"反事实"分支）
  4. 玩家做出选择 → 推演历史 → 新事件 → 新选项 …
  5. 直到「人类灭绝」才结束

依赖：
  pip install google-generativeai pyyaml networkx

用法：
  export GEMINI_API_KEY=""
  python play.py
"""

import os
import sys
import json
import textwrap
import google.generativeai as genai

# ── 路径设置 ─────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "knowledge_base", "scripts"))

from query_engine import QueryEngine

# ── 常量 ──────────────────────────────────────────────────
PROXY = os.environ.get("HTTP_PROXY", os.environ.get("HTTPS_PROXY", ""))
WIDTH = 72  # 终端显示宽度

# ── 颜色 (ANSI) ──────────────────────────────────────────
class C:
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    RESET   = "\033[0m"

def hr(char="─"):
    print(C.DIM + char * WIDTH + C.RESET)

def title(text):
    hr("═")
    print(C.BOLD + C.CYAN + text.center(WIDTH) + C.RESET)
    hr("═")

def wrap(text, indent=2):
    for line in textwrap.wrap(text, width=WIDTH - indent):
        print(" " * indent + line)

# ── Gemini 配置 ───────────────────────────────────────────
def setup_gemini() -> genai.GenerativeModel:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print(f"\n{C.YELLOW}未检测到 GEMINI_API_KEY 环境变量。{C.RESET}")
        api_key = input("请输入你的 Gemini API Key: ").strip()
        if not api_key:
            print(f"{C.RED}无法继续，需要 API Key。{C.RESET}")
            sys.exit(1)

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            top_p=0.95,
            max_output_tokens=2048,
        ),
    )
    return model

# ── 加载知识库上下文 ──────────────────────────────────────
def build_full_context(engine: QueryEngine, compound_id: str) -> str:
    """为选定化合物构建完整 Gemini 上下文（故事线 + 百科全文）"""
    return engine.build_gemini_context(
        compound_id,
        include_encyclopedia=True,
        include_graph=True,
    )

def build_all_compounds_brief(engine: QueryEngine) -> str:
    """所有化合物的简表，供跨化合物推演时使用"""
    lines = ["【全部化合物简表】"]
    for cid in engine.stats["compounds"]:
        node = engine.graph.nodes.get(cid, {})
        lines.append(
            f"- {node.get('name_zh', cid)} ({node.get('name_en', '')}), "
            f"发明年份: {node.get('year_invented', '?')}, "
            f"分类: {node.get('category', '?')}"
        )
    return "\n".join(lines)

# ── 系统提示词 ────────────────────────────────────────────
SYSTEM_PROMPT = """\
你是「Omphalina 历史物质模拟器」的叙事引擎。

## 角色
你是一位全知全能的历史演绎大师。你基于真实历史和提供的知识库数据，向玩家讲述化合物改变人类命运的故事，并在关键节点给出选择。

## 游戏规则
1. 每一轮你要：
   a) 用 2-4 段生动的中文描述当前历史时刻（年代、地点、人物、事件）
   b) 提出 3-4 个选项供玩家选择，格式:
      [1] 选项描述（简短）
      [2] 选项描述
      [3] 选项描述
   c) 选项中**至少一个**是真实历史走向，**至少一个**是合理的反事实推演
   d) 不要告诉玩家哪个是真实历史，哪个是反事实

2. 玩家选择后：
   - 如果选了**真实历史**：继续沿真实时间线推进
   - 如果选了**反事实**：基于合理推演展开平行历史，但最终会收敛回真实影响

3. 叙事风格：
   - 语言要**戏剧化、有画面感**，像纪录片旁白
   - 插入历史人物的引言或心理描写
   - 强调讽刺性和戏剧性转折
   - 适时加入其他化合物的交叉影响

4. 游戏终止条件：
   - 只有当推演结果导致**人类灭绝**时，才输出「☠️ 游戏结束：人类灭绝」
   - 只要人类还存续，游戏就必须继续
   - 反事实路线可能更快导致灭绝

5. 特殊标记：
   - 当事件涉及真实历史讽刺时，用「🔄 讽刺」标注
   - 当涉及跨化合物影响时，用「🔗 交叉」标注
   - 每轮结尾标注当前推演所处的年代

6. 安全：
   - 绝对不要描述化学合成方法、反应条件、配方
   - 保持学术/纪录片的叙事口吻

## 输出格式
每轮回复严格按此格式：

---
📅 [年代]　📍 [地点]

[叙事描述，2-4 段]

---
你的选择：
[1] ...
[2] ...
[3] ...
---
"""

# ── 游戏主循环 ────────────────────────────────────────────
def select_compound(engine: QueryEngine) -> str:
    """让玩家选择起始化合物"""
    title("⚗️  Omphalina — 历史物质模拟器")
    print()
    print(f"  {C.DIM}「每一种化合物，都是人类命运的一个分叉点。」{C.RESET}")
    print()
    hr()
    print(f"  {C.BOLD}选择你要探索的化合物：{C.RESET}")
    print()

    compounds = engine.stats["compounds"]
    for i, cid in enumerate(compounds, 1):
        node = engine.graph.nodes.get(cid, {})
        name = node.get("name_zh", cid)
        name_en = node.get("name_en", "")
        year = node.get("year_invented", "?")
        cat = node.get("category", "")
        print(f"  {C.YELLOW}[{i}]{C.RESET} {C.BOLD}{name}{C.RESET} ({name_en})")
        print(f"      {C.DIM}{year} · {cat}{C.RESET}")

    print()
    hr()

    while True:
        try:
            choice = input(f"\n  输入编号 (1-{len(compounds)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(compounds):
                return compounds[idx]
        except (ValueError, IndexError):
            pass
        print(f"  {C.RED}请输入 1-{len(compounds)} 之间的数字。{C.RESET}")


def play(engine: QueryEngine, model: genai.GenerativeModel, compound_id: str):
    """主游戏循环"""
    # 构建上下文
    print(f"\n  {C.DIM}正在加载知识库...{C.RESET}", end="", flush=True)
    compound_context = build_full_context(engine, compound_id)
    all_brief = build_all_compounds_brief(engine)
    print(f" ✅")

    compound_name = engine.graph.nodes[compound_id].get("name_zh", compound_id)

    title(f"⚗️  {compound_name} — 命运之旅")
    print()

    # 开始对话
    chat = model.start_chat(history=[])

    # 第一条消息：注入知识库 + 启动游戏
    first_message = f"""\
{SYSTEM_PROMPT}

## 知识库数据

{compound_context}

{all_brief}

---
请开始游戏。从这个化合物故事的**最早历史节点**开始叙事，给出第一轮选择。
"""

    print(f"  {C.DIM}AI 正在构思开场...{C.RESET}\n")

    try:
        response = chat.send_message(first_message)
    except Exception as e:
        print(f"\n{C.RED}  Gemini API 调用失败: {e}{C.RESET}")
        print(f"  {C.DIM}提示：检查 API Key 是否有效、网络是否通畅。{C.RESET}")
        return

    # 游戏循环
    round_num = 1
    while True:
        # 显示 AI 回复
        hr("─")
        print(f"  {C.MAGENTA}第 {round_num} 轮{C.RESET}")
        hr("─")
        print()
        print(response.text)
        print()

        # 检查游戏是否结束
        if "人类灭绝" in response.text and "游戏结束" in response.text:
            hr("═")
            print(f"\n  {C.RED}{C.BOLD}☠️  游戏结束 — 人类灭绝{C.RESET}")
            print(f"  {C.DIM}你在第 {round_num} 轮终结了人类文明。{C.RESET}\n")
            hr("═")
            break

        # 获取玩家输入
        while True:
            player_input = input(f"  {C.GREEN}你的选择 (输入编号，或输入文字自由回答): {C.RESET}").strip()
            if player_input:
                break
            print(f"  {C.DIM}请输入选择。{C.RESET}")

        if player_input.lower() in ("q", "quit", "exit", "退出"):
            print(f"\n  {C.DIM}游戏终止。{C.RESET}")
            break

        # 发送选择给 AI
        print(f"\n  {C.DIM}推演中...{C.RESET}\n")
        try:
            response = chat.send_message(
                f"玩家选择：{player_input}\n\n"
                f"请根据这个选择继续推演历史，给出下一轮叙事和选择。"
                f"记住：只有人类灭绝才能终止游戏。"
            )
        except Exception as e:
            print(f"\n{C.RED}  API 调用失败: {e}{C.RESET}")
            print(f"  {C.DIM}尝试重新发送...{C.RESET}")
            try:
                response = chat.send_message(
                    f"玩家选择：{player_input}\n请继续。"
                )
            except Exception as e2:
                print(f"\n{C.RED}  再次失败: {e2}{C.RESET}")
                break

        round_num += 1

    # 游戏总结
    print(f"\n  {C.BOLD}游戏统计：{C.RESET}")
    print(f"  化合物：{compound_name}")
    print(f"  进行了 {round_num} 轮推演")
    print()

    # 询问是否继续
    again = input(f"  再来一局？(y/n): ").strip().lower()
    if again in ("y", "yes", "是", "好"):
        return True
    return False


# ── 入口 ──────────────────────────────────────────────────
def main():
    # 代理设置（如需代理请设置 HTTP_PROXY / HTTPS_PROXY 环境变量）
    if PROXY:
        os.environ.setdefault("HTTP_PROXY", PROXY)
        os.environ.setdefault("HTTPS_PROXY", PROXY)

    # 初始化
    print(f"\n{C.DIM}  加载因果图...{C.RESET}", end="", flush=True)
    engine = QueryEngine()
    print(f" ✅ {engine.stats['total_nodes']} 节点, {engine.stats['total_edges']} 边")

    model = setup_gemini()

    # 游戏循环
    while True:
        compound_id = select_compound(engine)
        again = play(engine, model, compound_id)
        if not again:
            break

    print(f"\n  {C.DIM}感谢游玩 Omphalina 历史物质模拟器。{C.RESET}\n")


if __name__ == "__main__":
    main()
