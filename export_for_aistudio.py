#!/usr/bin/env python3
"""
Omphalina — 知识库导出工具 (面向 Google AI Studio)

将分散在 30+ 个文件中的知识库整合为 3 个文件：
  1. system_instructions.txt  → 粘贴到 AI Studio System Instructions 栏
  2. knowledge_base_full.md   → 上传为上下文文件（20 篇百科全文，零删减）
  3. storylines_full.md       → 上传为上下文文件（schema + 7 故事线 + 跨连接 + 图摘要）

运行:
  .venv/bin/python export_for_aistudio.py
"""

import os
import json
import glob
import yaml
import sys

# ── 路径 ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "knowledge_base")
ENCYCLOPEDIA_DIR = os.path.join(KB_DIR, "encyclopedia")
STORYLINES_DIR = os.path.join(KB_DIR, "storylines")
EXPORT_DIR = os.path.join(BASE_DIR, "aistudio_export")

os.makedirs(EXPORT_DIR, exist_ok=True)

# ── 工具函数 ──────────────────────────────────────────────
def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size = len(content)
    tokens_est = size // 4
    print(f"  ✅ {os.path.basename(path)}: {size:,} 字符 (~{tokens_est:,} tokens)")

# ══════════════════════════════════════════════════════════
# 1. System Instructions
# ══════════════════════════════════════════════════════════
def export_system_instructions():
    print("\n📝 生成 system_instructions.txt ...")

    text = """\
# Omphalina — 历史物质模拟器 · 系统指令

## 角色
你是「Omphalina 历史物质模拟器」的叙事引擎——一位全知全能的历史演绎大师。
你的上下文中包含 **完整的百科知识库** (knowledge_base_full.md) 和 **完整的故事线数据** (storylines_full.md)。
你必须始终基于这些数据进行叙事，不要编造不在知识库中的"历史事实"。

## 知识库结构说明
你的上下文包含两个数据文件：

### knowledge_base_full.md（第一层：百科搬运层）
- 7 个化合物的完整 Wikipedia 百科（中英双语），约 24 万 tokens
- 8 位关键人物传记
- 5 个历史专题条目
- 这是你的 **事实权威来源**，叙事时请引用其中的具体细节、年代、引语

### storylines_full.md（第二层：故事线创作层）
- Schema 定义：节点类型（Compound/Person/Event/Consequence）、边类型（INVENTED_BY/ENABLED/CAUSED/IRONIC_TWIST 等）
- 7 个化合物的故事线 YAML：每个包含关键人物、戏剧性事件、后果、因果链，每条边带有 drama_score 和 irony_level 评分
- 9 条跨化合物连接：描述化合物之间的关联
- 因果图统计摘要：高戏剧性边 TOP 列表、高讽刺性边 TOP 列表
- 这是你的 **叙事骨架**，优先选择 drama_score ≥ 0.85 的事件节点进行讲述

## 游戏规则
1. 每一轮你要：
   a) 用 2-4 段生动的中文描述当前历史时刻（年代、地点、人物、事件）
   b) 提出 3-4 个选项供玩家选择，格式:
      [1] 选项描述（简短）
      [2] 选项描述
      [3] 选项描述
   c) 选项中 **至少一个** 是真实历史走向，**至少一个** 是合理的反事实推演
   d) 不要告诉玩家哪个是真实历史，哪个是反事实

2. 玩家选择后：
   - 如果选了 **真实历史**：继续沿真实时间线推进到知识库中的下一个事件节点
   - 如果选了 **反事实**：基于合理推演展开平行历史，但最终会收敛回真实影响

3. 叙事风格：
   - 语言要 **戏剧化、有画面感**，像纪录片旁白
   - 引用知识库中的原始引语 (quote 字段) 和具体数据
   - 插入历史人物的引言或心理描写
   - 强调讽刺性 (irony_level ≥ 0.8 的边) 和戏剧性转折
   - 适时引入跨化合物连接 (cross_connections)，展示化合物之间的命运交织

4. 游戏终止条件：
   - 只有当推演结果导致 **人类灭绝** 时，才输出「☠️ 游戏结束：人类灭绝」
   - 只要人类还存续，游戏就必须继续给出新选项
   - 反事实路线可能更快导致灭绝

5. 特殊标记：
   - 当事件涉及真实历史讽刺时，用「🔄 讽刺」标注
   - 当涉及跨化合物影响时，用「🔗 交叉」标注
   - 每轮结尾标注当前推演所处的年代

6. 安全红线（绝对不可违反）：
   - 绝对不要描述化学合成方法、反应条件、配方、精确配比
   - 绝对不要提供原料采购或实验操作信息
   - 保持学术/纪录片的叙事口吻
   - 探索物质的 **历史与哲学**，绝不提供"如何制造"的指导

## 输出格式
每轮回复严格按此格式：

---
📅 [年代]　📍 [地点]

[叙事描述，2-4 段，引用知识库中的具体细节]

---
你的选择：
[1] ...
[2] ...
[3] ...
---

## 开场方式
当用户指定一个化合物后，从该化合物故事线的 **最早事件节点** 开始叙事。
如果用户没有指定，列出全部 7 个化合物供选择：
1. 阿司匹林 (1897) — 最古老万能药
2. 合成氨 (1909) — 养活40亿人 ↔ 化学武器
3. 塑料 (1907) — 材料革命 ↔ 全球污染
4. DDT (1939) — 诺贝尔灭疟 ↔ 环保运动
5. 氟利昂 (1928) — 完美制冷剂 ↔ 臭氧层空洞
6. 青霉素 (1942) — 拯救千万生命 ↔ 超级细菌
7. 味精 (1908) — 鲜味科学 ↔ 种族偏见
"""

    write_file(os.path.join(EXPORT_DIR, "system_instructions.txt"), text)

# ══════════════════════════════════════════════════════════
# 2. Knowledge Base Full (百科全文合并)
# ══════════════════════════════════════════════════════════
def export_knowledge_base():
    print("\n📚 生成 knowledge_base_full.md ...")

    parts = []

    # 标题
    parts.append("# Omphalina 全景知识库 — 第一层：百科搬运层\n")
    parts.append("> 数据来源：Wikipedia EN/ZH · 自动拉取于 2026-02-07")
    parts.append("> 内容：7 化合物 + 5 专题 + 8 人物传记 · 约 686,000 字符 · ~240,000 tokens")
    parts.append("> 完整性：全文零删减，保留原始章节结构\n")
    parts.append("---\n")

    # ── 化合物百科 ────────────────────────────────────────
    parts.append("# PART 1: 化合物百科 (7 篇)\n")

    compound_order = ["aspirin", "synthetic_ammonia", "plastics", "ddt", "cfc", "penicillin", "msg"]
    compound_names = {
        "aspirin": "阿司匹林", "synthetic_ammonia": "合成氨",
        "plastics": "塑料", "ddt": "DDT", "cfc": "氟利昂 (CFC)",
        "penicillin": "青霉素", "msg": "味精 (MSG)"
    }

    for cid in compound_order:
        filepath = os.path.join(ENCYCLOPEDIA_DIR, "compounds", f"{cid}.md")
        if os.path.exists(filepath):
            content = read_file(filepath)
            parts.append(f"\n{'=' * 80}")
            parts.append(f"## 化合物：{compound_names.get(cid, cid)}")
            parts.append(f"{'=' * 80}\n")
            parts.append(content)
            parts.append("\n---\n")
            print(f"    ✓ {cid}.md ({len(content):,} 字符)")

    # ── 历史专题 ──────────────────────────────────────────
    parts.append("\n# PART 2: 历史专题 (5 篇)\n")

    topics_dir = os.path.join(ENCYCLOPEDIA_DIR, "topics")
    for filepath in sorted(glob.glob(os.path.join(topics_dir, "*.md"))):
        fname = os.path.basename(filepath)
        content = read_file(filepath)
        parts.append(f"\n{'=' * 80}")
        parts.append(f"## 专题：{fname.replace('.md', '').replace('_', ' ').title()}")
        parts.append(f"{'=' * 80}\n")
        parts.append(content)
        parts.append("\n---\n")
        print(f"    ✓ {fname} ({len(content):,} 字符)")

    # ── 人物传记 ──────────────────────────────────────────
    parts.append("\n# PART 3: 关键人物传记 (8 篇)\n")

    people_dir = os.path.join(ENCYCLOPEDIA_DIR, "people")
    for filepath in sorted(glob.glob(os.path.join(people_dir, "*.md"))):
        fname = os.path.basename(filepath)
        content = read_file(filepath)
        parts.append(f"\n{'=' * 80}")
        parts.append(f"## 人物：{fname.replace('.md', '').replace('_', ' ').title()}")
        parts.append(f"{'=' * 80}\n")
        parts.append(content)
        parts.append("\n---\n")
        print(f"    ✓ {fname} ({len(content):,} 字符)")

    full_text = "\n".join(parts)
    write_file(os.path.join(EXPORT_DIR, "knowledge_base_full.md"), full_text)

# ══════════════════════════════════════════════════════════
# 3. Storylines Full (故事线 + 图摘要合并)
# ══════════════════════════════════════════════════════════
def export_storylines():
    print("\n🎭 生成 storylines_full.md ...")

    parts = []

    parts.append("# Omphalina 故事线数据 — 第二层：LLM 创作层\n")
    parts.append("> 内容：Schema 定义 + 7 化合物故事线 YAML + 跨化合物连接 + 因果图摘要")
    parts.append("> 用途：叙事引擎的结构化骨架，每条因果边带有 drama_score 和 irony_level 评分\n")
    parts.append("---\n")

    # ── Schema ────────────────────────────────────────────
    parts.append("# PART 1: 数据结构定义 (Schema)\n")
    parts.append("```yaml")
    parts.append(read_file(os.path.join(STORYLINES_DIR, "schema.yaml")))
    parts.append("```\n")
    parts.append("---\n")
    print("    ✓ schema.yaml")

    # ── 7 个化合物故事线 ──────────────────────────────────
    parts.append("# PART 2: 化合物故事线 (7 篇)\n")

    compound_order = ["aspirin", "synthetic_ammonia", "plastics", "ddt", "cfc", "penicillin", "msg"]
    compounds_dir = os.path.join(STORYLINES_DIR, "compounds")

    for cid in compound_order:
        filepath = os.path.join(compounds_dir, f"{cid}.yaml")
        if os.path.exists(filepath):
            content = read_file(filepath)
            parts.append(f"\n{'=' * 80}")
            parts.append(f"## 故事线：{cid}")
            parts.append(f"{'=' * 80}\n")
            parts.append("```yaml")
            parts.append(content)
            parts.append("```\n")
            parts.append("---\n")
            print(f"    ✓ {cid}.yaml ({len(content):,} 字符)")

    # ── 跨化合物连接 ──────────────────────────────────────
    parts.append("# PART 3: 跨化合物因果连接\n")
    parts.append("```yaml")
    parts.append(read_file(os.path.join(STORYLINES_DIR, "cross_connections.yaml")))
    parts.append("```\n")
    parts.append("---\n")
    print("    ✓ cross_connections.yaml")

    # ── 因果图统计摘要 ────────────────────────────────────
    parts.append("# PART 4: 因果图统计摘要\n")
    parts.append(build_graph_summary())
    parts.append("\n---\n")
    print("    ✓ graph summary (从 graph_export.json 提取)")

    full_text = "\n".join(parts)
    write_file(os.path.join(EXPORT_DIR, "storylines_full.md"), full_text)


def build_graph_summary():
    """从 graph_export.json 提取关键统计，避免上传 3161 行原始 JSON"""
    json_path = os.path.join(STORYLINES_DIR, "graph_export.json")
    if not os.path.exists(json_path):
        return "> ⚠️ graph_export.json 未找到，请先运行 graph_builder.py\n"

    with open(json_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    # 节点统计
    node_types = {}
    for n in nodes:
        nt = n.get("node_type", "Unknown")
        node_types[nt] = node_types.get(nt, 0) + 1

    # 边统计
    edge_types = {}
    high_drama = []
    high_irony = []

    for e in links:
        et = e.get("edge_type", "Unknown")
        edge_types[et] = edge_types.get(et, 0) + 1

        drama = e.get("drama_score", 0)
        irony = e.get("irony_level", 0)

        source_id = e.get("source", "?")
        target_id = e.get("target", "?")

        # 找到节点名
        source_name = source_id
        target_name = target_id
        for n in nodes:
            if n.get("id") == source_id:
                source_name = n.get("name_zh", n.get("description_zh", source_id))
            if n.get("id") == target_id:
                target_name = n.get("name_zh", n.get("description_zh", target_id))

        desc = e.get("description_zh", e.get("relationship_zh", ""))

        if drama and drama >= 0.85:
            high_drama.append({
                "source": source_name, "target": target_name,
                "drama": drama, "irony": irony or 0,
                "type": et, "desc": desc
            })
        if irony and irony >= 0.85:
            high_irony.append({
                "source": source_name, "target": target_name,
                "drama": drama or 0, "irony": irony,
                "type": et, "desc": desc
            })

    high_drama.sort(key=lambda x: x["drama"], reverse=True)
    high_irony.sort(key=lambda x: x["irony"], reverse=True)

    lines = []
    lines.append("以下是从 NetworkX 因果图导出的统计摘要（原始图包含 125 节点、132 边）：\n")

    lines.append("## 节点统计")
    lines.append(f"- 总节点数: **{len(nodes)}**")
    for nt, count in sorted(node_types.items()):
        lines.append(f"  - {nt}: {count}")

    lines.append(f"\n## 边统计")
    lines.append(f"- 总边数: **{len(links)}**")
    for et, count in sorted(edge_types.items()):
        lines.append(f"  - {et}: {count}")

    lines.append(f"\n## 高戏剧性因果边 TOP {min(25, len(high_drama))} (drama_score ≥ 0.85)")
    lines.append("| # | 源节点 | → | 目标节点 | Drama | Irony | 类型 | 描述 |")
    lines.append("|---|--------|---|----------|-------|-------|------|------|")
    for i, e in enumerate(high_drama[:25], 1):
        desc_short = e["desc"][:50] + "…" if len(e["desc"]) > 50 else e["desc"]
        lines.append(f"| {i} | {e['source']} | → | {e['target']} | {e['drama']:.2f} | {e['irony']:.2f} | {e['type']} | {desc_short} |")

    lines.append(f"\n## 高讽刺性因果边 TOP {min(20, len(high_irony))} (irony_level ≥ 0.85)")
    lines.append("| # | 源节点 | → | 目标节点 | Irony | Drama | 类型 | 描述 |")
    lines.append("|---|--------|---|----------|-------|-------|------|------|")
    for i, e in enumerate(high_irony[:20], 1):
        desc_short = e["desc"][:50] + "…" if len(e["desc"]) > 50 else e["desc"]
        lines.append(f"| {i} | {e['source']} | → | {e['target']} | {e['irony']:.2f} | {e['drama']:.2f} | {e['type']} | {desc_short} |")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("Omphalina — 知识库导出 (面向 Google AI Studio)")
    print("=" * 60)

    export_system_instructions()
    export_knowledge_base()
    export_storylines()

    # 最终汇总
    print("\n" + "=" * 60)
    print("📦 导出完成！文件位于:")
    print(f"   {EXPORT_DIR}/")

    total_chars = 0
    for fname in ["system_instructions.txt", "knowledge_base_full.md", "storylines_full.md"]:
        fpath = os.path.join(EXPORT_DIR, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            total_chars += size

    print(f"\n   总计: {total_chars:,} 字节 (~{total_chars // 4:,} tokens)")
    print(f"   Gemini 1M 上下文占比: ~{total_chars // 4 / 10000:.1f}%")

    print(f"""
📋 AI Studio 操作步骤:
   1. 打开 aistudio.google.com → 新建 Chat
   2. 将 system_instructions.txt 粘贴到 System Instructions 栏
   3. 上传 knowledge_base_full.md 和 storylines_full.md 作为上下文
   4. 在聊天框发送开场 prompt
""")


if __name__ == "__main__":
    main()
