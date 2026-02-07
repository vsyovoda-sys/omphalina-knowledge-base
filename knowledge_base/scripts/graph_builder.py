#!/usr/bin/env python3
"""
Omphalina 知识库 — 因果图构建器

读取 storylines/compounds/*.yaml 和 cross_connections.yaml，
构建 NetworkX 有向图 (DiGraph)，供 query_engine.py 使用。

用法:
    from graph_builder import build_graph, load_graph_from_storylines
    G = load_graph_from_storylines()
"""

import os
import glob
import yaml
import networkx as nx
from typing import Any

# ============================================================
# 配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORYLINES_DIR = os.path.join(BASE_DIR, "storylines", "compounds")
CROSS_CONNECTIONS_PATH = os.path.join(BASE_DIR, "storylines", "cross_connections.yaml")


# ============================================================
# 图构建
# ============================================================

def load_yaml(filepath: str) -> dict:
    """安全加载 YAML 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def add_compound_to_graph(G: nx.DiGraph, data: dict) -> None:
    """
    将一个化合物的故事线数据添加到图中。

    期望的 YAML 结构:
    compound:
      id: aspirin
      name_zh: 阿司匹林
      ...
      people: [...]
      events: [...]
      consequences: [...]
      causal_chains: [...]
    """
    compound = data.get("compound", {})
    compound_id = compound.get("id")
    if not compound_id:
        return

    # 添加化合物节点
    G.add_node(compound_id,
               node_type="Compound",
               name_zh=compound.get("name_zh", ""),
               name_en=compound.get("name_en", ""),
               aliases_zh=compound.get("aliases_zh", []),
               category=compound.get("category", ""),
               year_invented=compound.get("year_invented"),
               formula=compound.get("formula", ""),
               safety_note=compound.get("safety_note", ""))

    # 添加人物节点 + INVENTED_BY 边
    for person in compound.get("people", []):
        person_id = person.get("id")
        if not person_id:
            continue
        G.add_node(person_id,
                   node_type="Person",
                   name_zh=person.get("name_zh", ""),
                   name_en=person.get("name_en", ""),
                   role=person.get("role", ""),
                   birth_year=person.get("birth_year"),
                   death_year=person.get("death_year"),
                   nationality=person.get("nationality", ""),
                   nobel_year=person.get("nobel_year"),
                   irony_note=person.get("irony_note", ""))

        G.add_edge(compound_id, person_id,
                   edge_type="INVENTED_BY",
                   year=person.get("year"),
                   context=person.get("context", ""))

    # 添加事件节点
    for event in compound.get("events", []):
        event_id = event.get("id")
        if not event_id:
            continue
        G.add_node(event_id,
                   node_type="Event",
                   name_zh=event.get("name_zh", ""),
                   name_en=event.get("name_en", ""),
                   year=event.get("year"),
                   end_year=event.get("end_year"),
                   domain=event.get("domain", ""),
                   location=event.get("location", ""),
                   scale=event.get("scale", ""),
                   quote=event.get("quote", ""),
                   source_ref=event.get("source_ref", ""))

    # 添加后果节点
    for consequence in compound.get("consequences", []):
        cons_id = consequence.get("id")
        if not cons_id:
            continue
        G.add_node(cons_id,
                   node_type="Consequence",
                   description_zh=consequence.get("description_zh", ""),
                   description_en=consequence.get("description_en", ""),
                   type=consequence.get("type", ""),
                   domain=consequence.get("domain", ""),
                   scale=consequence.get("scale", ""),
                   ongoing=consequence.get("ongoing", False),
                   quantifier=consequence.get("quantifier", ""))

    # 添加因果链（边）
    for chain in compound.get("causal_chains", []):
        source = chain.get("source", compound_id)
        target = chain.get("target")
        if not target:
            continue

        edge_type = chain.get("type", "ENABLED")
        G.add_edge(source, target,
                   edge_type=edge_type,
                   drama_score=chain.get("drama_score", 0.5),
                   irony_level=chain.get("irony_level", 0.5),
                   time_lag_years=chain.get("time_lag_years"),
                   domains=chain.get("domains", []),
                   description_zh=chain.get("description_zh", ""),
                   description_en=chain.get("description_en", ""))


def add_cross_connections(G: nx.DiGraph, data: dict) -> None:
    """添加跨化合物连接"""
    for conn in data.get("connections", []):
        source = conn.get("source_compound")
        target = conn.get("target_compound")
        if not source or not target:
            continue

        G.add_edge(source, target,
                   edge_type="CROSS_CONNECTION",
                   connection_type=conn.get("connection_type", ""),
                   relationship_zh=conn.get("relationship_zh", ""),
                   relationship_en=conn.get("relationship_en", ""),
                   drama_score=conn.get("drama_score", 0.5),
                   bidirectional=conn.get("bidirectional", True))

        # 如果是双向连接，添加反向边
        if conn.get("bidirectional", True):
            G.add_edge(target, source,
                       edge_type="CROSS_CONNECTION",
                       connection_type=conn.get("connection_type", ""),
                       relationship_zh=conn.get("relationship_zh", ""),
                       relationship_en=conn.get("relationship_en", ""),
                       drama_score=conn.get("drama_score", 0.5),
                       bidirectional=True)


# ============================================================
# 公共接口
# ============================================================

def load_graph_from_storylines() -> nx.DiGraph:
    """
    从 storylines/ 目录加载所有数据，构建并返回完整的因果图。
    这是外部模块（如 query_engine.py）调用的主入口。
    """
    G = nx.DiGraph()

    # 加载所有化合物故事线
    yaml_files = glob.glob(os.path.join(STORYLINES_DIR, "*.yaml"))
    for filepath in sorted(yaml_files):
        data = load_yaml(filepath)
        add_compound_to_graph(G, data)

    # 加载跨化合物连接
    if os.path.exists(CROSS_CONNECTIONS_PATH):
        cross_data = load_yaml(CROSS_CONNECTIONS_PATH)
        add_cross_connections(G, cross_data)

    return G


def get_graph_stats(G: nx.DiGraph) -> dict:
    """获取图的统计信息"""
    node_types = {}
    for _, attrs in G.nodes(data=True):
        nt = attrs.get("node_type", "Unknown")
        node_types[nt] = node_types.get(nt, 0) + 1

    edge_types = {}
    for _, _, attrs in G.edges(data=True):
        et = attrs.get("edge_type", "Unknown")
        edge_types[et] = edge_types.get(et, 0) + 1

    # 高戏剧性边
    high_drama = [(u, v, d) for u, v, d in G.edges(data=True)
                  if d.get("drama_score", 0) >= 0.9]

    # 高讽刺性边
    high_irony = [(u, v, d) for u, v, d in G.edges(data=True)
                  if d.get("irony_level", 0) >= 0.9]

    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": node_types,
        "edge_types": edge_types,
        "high_drama_edges": len(high_drama),
        "high_irony_edges": len(high_irony),
        "connected_components": nx.number_weakly_connected_components(G),
        "compounds": [n for n, d in G.nodes(data=True) if d.get("node_type") == "Compound"],
    }


def export_graph_json(G: nx.DiGraph, filepath: str) -> None:
    """将图导出为 JSON 格式（可用于前端可视化）"""
    import json
    from networkx.readwrite import json_graph
    data = json_graph.node_link_data(G)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 主流程（直接运行时用于验证）
# ============================================================

def main():
    print("=" * 60)
    print("Omphalina — 因果图构建与验证")
    print("=" * 60)

    G = load_graph_from_storylines()
    stats = get_graph_stats(G)

    print(f"\n📊 图统计:")
    print(f"  节点总数: {stats['total_nodes']}")
    print(f"  边总数:   {stats['total_edges']}")
    print(f"\n  节点类型分布:")
    for nt, count in sorted(stats["node_types"].items()):
        print(f"    {nt}: {count}")
    print(f"\n  边类型分布:")
    for et, count in sorted(stats["edge_types"].items()):
        print(f"    {et}: {count}")
    print(f"\n  高戏剧性边 (≥0.9): {stats['high_drama_edges']}")
    print(f"  高讽刺性边 (≥0.9): {stats['high_irony_edges']}")
    print(f"  弱连通分量数: {stats['connected_components']}")
    print(f"  化合物列表: {stats['compounds']}")

    if stats["total_nodes"] == 0:
        print("\n⚠️ 图为空！请先在 storylines/compounds/ 中创建故事线 YAML 文件。")
    else:
        # 导出 JSON
        export_path = os.path.join(BASE_DIR, "storylines", "graph_export.json")
        export_graph_json(G, export_path)
        print(f"\n  图已导出: {export_path}")

    print("=" * 60)


if __name__ == "__main__":
    main()
