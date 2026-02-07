#!/usr/bin/env python3
"""
Omphalina 知识库 — 查询引擎

基于 NetworkX 因果图和全景知识库，提供核心查询功能：
1. 按 drama_score 排序的涟漪效应
2. 最讽刺的因果路径
3. 跨化合物因果链发现
4. 为 Gemini prompt 构建上下文

用法:
    from query_engine import QueryEngine
    engine = QueryEngine()
    result = engine.most_dramatic_ripples("aspirin", top_n=5)
"""

import os
import glob
import networkx as nx
from typing import Any

# 同级模块导入
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graph_builder import load_graph_from_storylines, get_graph_stats

# ============================================================
# 配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCYCLOPEDIA_DIR = os.path.join(BASE_DIR, "encyclopedia", "compounds")


class QueryEngine:
    """
    Omphalina 查询引擎

    提供因果图遍历和知识库检索功能，
    输出可直接用于 Gemini prompt 的结构化上下文。
    """

    def __init__(self):
        self.graph = load_graph_from_storylines()
        self.stats = get_graph_stats(self.graph)

    def reload(self):
        """重新加载图数据"""
        self.graph = load_graph_from_storylines()
        self.stats = get_graph_stats(self.graph)

    # ========================================================
    # 核心查询
    # ========================================================

    def most_dramatic_ripples(self, compound_id: str, top_n: int = 5) -> list[dict]:
        """
        从指定化合物出发，找到 drama_score 最高的涟漪效应链。

        返回:
            按 drama_score 降序排列的因果边列表。
        """
        if compound_id not in self.graph:
            return []

        ripples = []
        # BFS 遍历从化合物出发的所有可达边
        for u, v, data in self.graph.edges(data=True):
            # 只关注从此化合物可达的边
            if nx.has_path(self.graph, compound_id, u) or u == compound_id:
                drama = data.get("drama_score", 0)
                if drama > 0:
                    # 计算因果距离
                    try:
                        distance = nx.shortest_path_length(self.graph, compound_id, u)
                    except nx.NetworkXNoPath:
                        distance = -1

                    ripples.append({
                        "source": u,
                        "target": v,
                        "source_name": self.graph.nodes[u].get("name_zh", u),
                        "target_name": self.graph.nodes[v].get("name_zh",
                                       self.graph.nodes[v].get("description_zh", v)),
                        "drama_score": drama,
                        "irony_level": data.get("irony_level", 0),
                        "edge_type": data.get("edge_type", ""),
                        "description_zh": data.get("description_zh", ""),
                        "domains": data.get("domains", []),
                        "causal_distance": distance,
                    })

        # 按 drama_score 降序排列
        ripples.sort(key=lambda x: x["drama_score"], reverse=True)
        return ripples[:top_n]

    def most_ironic_paths(self, compound_id: str, top_n: int = 3) -> list[dict]:
        """
        找到从指定化合物出发的最讽刺因果路径。

        返回:
            路径列表，每条路径包含完整的节点序列和累积讽刺性。
        """
        if compound_id not in self.graph:
            return []

        ironic_paths = []

        # 遍历所有从化合物可达的节点
        for target in self.graph.nodes():
            if target == compound_id:
                continue
            try:
                paths = list(nx.all_simple_paths(self.graph, compound_id, target, cutoff=5))
                for path in paths:
                    # 计算路径上的累积讽刺性
                    total_irony = 0
                    max_irony = 0
                    edges_info = []
                    for i in range(len(path) - 1):
                        edge_data = self.graph.get_edge_data(path[i], path[i + 1])
                        if edge_data:
                            irony = edge_data.get("irony_level", 0)
                            total_irony += irony
                            max_irony = max(max_irony, irony)
                            edges_info.append({
                                "from": path[i],
                                "to": path[i + 1],
                                "irony_level": irony,
                                "description_zh": edge_data.get("description_zh", ""),
                            })

                    if total_irony > 0:
                        ironic_paths.append({
                            "path": path,
                            "path_names": [self.graph.nodes[n].get("name_zh",
                                          self.graph.nodes[n].get("description_zh", n))
                                          for n in path],
                            "total_irony": total_irony,
                            "max_irony": max_irony,
                            "avg_irony": total_irony / len(edges_info) if edges_info else 0,
                            "length": len(path),
                            "edges": edges_info,
                        })
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        ironic_paths.sort(key=lambda x: x["avg_irony"], reverse=True)
        return ironic_paths[:top_n]

    def cross_compound_chains(self, source_compound: str, target_compound: str,
                               max_depth: int = 4) -> list[dict]:
        """
        找到两个化合物之间的因果链。

        返回:
            连接两个化合物的所有路径。
        """
        if source_compound not in self.graph or target_compound not in self.graph:
            return []

        chains = []
        try:
            paths = list(nx.all_simple_paths(
                self.graph, source_compound, target_compound, cutoff=max_depth
            ))
            for path in paths:
                drama_scores = []
                for i in range(len(path) - 1):
                    edge_data = self.graph.get_edge_data(path[i], path[i + 1])
                    if edge_data:
                        drama_scores.append(edge_data.get("drama_score", 0))

                chains.append({
                    "path": path,
                    "path_names": [self.graph.nodes[n].get("name_zh",
                                  self.graph.nodes[n].get("description_zh", n))
                                  for n in path],
                    "length": len(path),
                    "avg_drama": sum(drama_scores) / len(drama_scores) if drama_scores else 0,
                    "total_drama": sum(drama_scores),
                })
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        chains.sort(key=lambda x: x["avg_drama"], reverse=True)
        return chains

    def get_compound_summary(self, compound_id: str) -> dict:
        """
        获取化合物的故事线摘要（用于 Gemini prompt）。
        """
        if compound_id not in self.graph:
            return {}

        node = self.graph.nodes[compound_id]
        out_edges = list(self.graph.out_edges(compound_id, data=True))

        # 关联人物
        people = [
            {"name": self.graph.nodes[v].get("name_zh", v),
             "role": self.graph.nodes[v].get("role", ""),
             "irony_note": self.graph.nodes[v].get("irony_note", "")}
            for _, v, d in out_edges
            if d.get("edge_type") == "INVENTED_BY"
        ]

        # 高戏剧性事件
        dramatic_events = sorted(
            [{"target": v,
              "name": self.graph.nodes[v].get("name_zh", v),
              "drama_score": d.get("drama_score", 0),
              "irony_level": d.get("irony_level", 0),
              "description": d.get("description_zh", "")}
             for _, v, d in out_edges
             if d.get("edge_type") in ("ENABLED", "CAUSED")],
            key=lambda x: x["drama_score"],
            reverse=True
        )

        return {
            "id": compound_id,
            "name_zh": node.get("name_zh", ""),
            "name_en": node.get("name_en", ""),
            "year": node.get("year_invented"),
            "category": node.get("category", ""),
            "people": people,
            "top_dramatic_events": dramatic_events[:5],
            "total_connections": len(out_edges),
        }

    # ========================================================
    # 全景知识库检索
    # ========================================================

    def load_encyclopedia_entry(self, compound_id: str) -> str:
        """
        加载化合物的全景知识库条目（Markdown 全文）。
        用于注入 Gemini 上下文。
        """
        filepath = os.path.join(ENCYCLOPEDIA_DIR, f"{compound_id}.md")
        if not os.path.exists(filepath):
            return ""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def load_all_encyclopedia(self) -> str:
        """
        加载所有化合物的全景知识库条目。
        警告: 约 25 万 token，仅在 Gemini 上下文足够时使用。
        """
        all_text = ""
        md_files = sorted(glob.glob(os.path.join(ENCYCLOPEDIA_DIR, "*.md")))
        for filepath in md_files:
            with open(filepath, "r", encoding="utf-8") as f:
                all_text += f.read() + "\n\n---\n\n"
        return all_text

    # ========================================================
    # Gemini Prompt 构建
    # ========================================================

    def build_gemini_context(self, compound_id: str,
                              include_encyclopedia: bool = True,
                              include_graph: bool = True) -> str:
        """
        为 Gemini API 构建完整的上下文。

        Args:
            compound_id: 化合物 ID
            include_encyclopedia: 是否包含全景知识库条目
            include_graph: 是否包含因果图数据

        Returns:
            格式化的上下文字符串，可直接作为 Gemini system prompt 的一部分。
        """
        parts = []

        # 安全护栏
        parts.append("""【安全指令】
你是一个历史物质模拟器。你只讨论化合物的历史、社会影响和哲学意义。
你绝对不能提供：合成方法、反应条件、精确配比、实验操作流程、原料采购信息。
如果用户询问"如何制造/合成"某化合物，请礼貌拒绝并引导回历史话题。
""")

        # 因果图数据
        if include_graph:
            summary = self.get_compound_summary(compound_id)
            if summary:
                parts.append(f"\n【故事线数据 — {summary.get('name_zh', compound_id)}】")
                parts.append(f"化合物: {summary['name_zh']} ({summary['name_en']})")
                parts.append(f"发明年份: {summary.get('year', 'N/A')}")
                parts.append(f"分类: {summary.get('category', 'N/A')}")

                if summary["people"]:
                    parts.append("\n关键人物:")
                    for p in summary["people"]:
                        line = f"  - {p['name']} ({p['role']})"
                        if p.get("irony_note"):
                            line += f" — 讽刺: {p['irony_note']}"
                        parts.append(line)

                if summary["top_dramatic_events"]:
                    parts.append("\n高戏剧性事件 (按 drama_score 降序):")
                    for e in summary["top_dramatic_events"]:
                        parts.append(
                            f"  - [{e['drama_score']:.2f}] {e['name']}: {e['description']}"
                        )

                # 最讽刺的路径
                ironic = self.most_ironic_paths(compound_id, top_n=2)
                if ironic:
                    parts.append("\n最讽刺的因果路径:")
                    for path in ironic:
                        parts.append(f"  路径: {' → '.join(path['path_names'])}")
                        parts.append(f"  平均讽刺性: {path['avg_irony']:.2f}")

        # 全景知识库
        if include_encyclopedia:
            entry = self.load_encyclopedia_entry(compound_id)
            if entry:
                parts.append(f"\n\n【全景知识库 — {compound_id}】")
                parts.append(entry)

        return "\n".join(parts)


# ============================================================
# 主流程（直接运行时用于测试）
# ============================================================

def main():
    print("=" * 60)
    print("Omphalina — 查询引擎测试")
    print("=" * 60)

    engine = QueryEngine()

    print(f"\n图状态: {engine.stats['total_nodes']} 节点, {engine.stats['total_edges']} 边")
    print(f"化合物: {engine.stats['compounds']}")

    if engine.stats["total_nodes"] == 0:
        print("\n⚠️ 图为空。请先创建故事线 YAML 文件 (storylines/compounds/*.yaml)")
        print("  然后运行此脚本进行测试。")
        print("\n📖 但全景知识库可用！测试知识库加载:")

        for compound_id in ["aspirin", "synthetic_ammonia", "plastics", "ddt",
                           "cfc", "penicillin", "msg"]:
            entry = engine.load_encyclopedia_entry(compound_id)
            if entry:
                print(f"  ✅ {compound_id}.md: {len(entry):,} 字符")
            else:
                print(f"  ❌ {compound_id}.md: 未找到")
        return

    # 如果图有数据，运行完整测试
    for compound_id in engine.stats["compounds"]:
        print(f"\n{'─' * 40}")
        print(f"🔍 化合物: {compound_id}")

        # 涟漪效应
        ripples = engine.most_dramatic_ripples(compound_id)
        if ripples:
            print(f"  最高戏剧性涟漪:")
            for r in ripples[:3]:
                print(f"    [{r['drama_score']:.2f}] {r['source_name']} → {r['target_name']}")
                print(f"           {r['description_zh']}")

        # 讽刺路径
        ironic = engine.most_ironic_paths(compound_id)
        if ironic:
            print(f"  最讽刺路径:")
            for p in ironic[:2]:
                print(f"    讽刺度 {p['avg_irony']:.2f}: {' → '.join(p['path_names'])}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
