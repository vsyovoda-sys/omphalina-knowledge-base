#!/usr/bin/env python3
"""
Omphalina 知识库 — Wikidata 结构化数据拉取脚本

从 Wikidata 拉取化合物的结构化元数据（化学式、CAS号、发明年份、发明者等），
注入到 encyclopedia/compounds/*.md 文件的"基本信息"章节。
"""

import os
import json
import re
from SPARQLWrapper import SPARQLWrapper, JSON

# ============================================================
# 配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOUNDS_DIR = os.path.join(BASE_DIR, "encyclopedia", "compounds")

PROXY = os.environ.get("HTTP_PROXY", os.environ.get("HTTPS_PROXY", ""))

# Wikidata 实体 ID 映射
# (文件名, Wikidata QID, 中文名, 英文名)
COMPOUND_WIKIDATA = [
    ("aspirin",           "Q18216",   "阿司匹林",     "Aspirin"),
    ("synthetic_ammonia", "Q191739",  "哈伯法/合成氨", "Haber Process"),
    ("plastics",          "Q11474",   "塑料",         "Plastic"),
    ("ddt",               "Q407258",  "DDT/滴滴涕",   "DDT"),
    ("cfc",               "Q134783",  "氯氟烃/氟利昂", "Chlorofluorocarbon"),
    ("penicillin",        "Q12198",   "青霉素",       "Penicillin"),
    ("msg",               "Q188539",  "味精/谷氨酸钠", "Monosodium Glutamate"),
]


# ============================================================
# Wikidata SPARQL 查询
# ============================================================

def query_wikidata(qid: str) -> dict:
    """
    从 Wikidata 查询化合物的结构化元数据。
    """
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    # 设置代理
    import urllib.request
    proxy_handler = urllib.request.ProxyHandler({
        'http': PROXY,
        'https': PROXY,
    })
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)

    query = f"""
    SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {{
      VALUES ?property {{
        wdt:P274    # 分子式 (molecular formula)
        wdt:P231    # CAS号
        wdt:P575    # 发现/发明时间
        wdt:P61     # 发现者/发明者
        wdt:P366    # 用途
        wdt:P31     # 实例属于
        wdt:P279    # 子类属于
        wdt:P1748   # NCI Thesaurus ID
        wdt:P486    # MeSH descriptor ID
      }}
      wd:{qid} ?property ?value.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en". }}
    }}
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.addCustomHttpHeader("User-Agent", "OmphalinaKnowledgeBase/1.0")

    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"  ⚠️ SPARQL 查询失败 ({qid}): {e}")
        return {"results": {"bindings": []}}


def query_compound_details(qid: str) -> dict:
    """
    用更精准的 SPARQL 查询化合物关键属性。
    """
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    query = f"""
    SELECT
      ?formula
      ?cas
      ?discoveryDate
      ?inventorLabel
      ?useLabel
      ?description
    WHERE {{
      OPTIONAL {{ wd:{qid} wdt:P274 ?formula. }}
      OPTIONAL {{ wd:{qid} wdt:P231 ?cas. }}
      OPTIONAL {{ wd:{qid} wdt:P575 ?discoveryDate. }}
      OPTIONAL {{ wd:{qid} wdt:P61 ?inventor. }}
      OPTIONAL {{ wd:{qid} wdt:P366 ?use. }}
      OPTIONAL {{ wd:{qid} schema:description ?description FILTER(LANG(?description) = "zh"). }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en". }}
    }}
    LIMIT 50
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.addCustomHttpHeader("User-Agent", "OmphalinaKnowledgeBase/1.0")

    try:
        results = sparql.query().convert()
        return parse_compound_results(results)
    except Exception as e:
        print(f"  ⚠️ SPARQL 查询失败 ({qid}): {e}")
        return {}


def parse_compound_results(results: dict) -> dict:
    """解析 SPARQL 结果为简洁的字典"""
    data = {
        "formula": None,
        "cas": None,
        "discovery_date": None,
        "inventors": set(),
        "uses": set(),
        "description_zh": None,
    }

    for binding in results.get("results", {}).get("bindings", []):
        if "formula" in binding and not data["formula"]:
            data["formula"] = binding["formula"]["value"]
        if "cas" in binding and not data["cas"]:
            data["cas"] = binding["cas"]["value"]
        if "discoveryDate" in binding and not data["discovery_date"]:
            raw_date = binding["discoveryDate"]["value"]
            # 提取年份
            match = re.match(r"(\d{4})", raw_date)
            if match:
                data["discovery_date"] = match.group(1)
        if "inventorLabel" in binding:
            data["inventors"].add(binding["inventorLabel"]["value"])
        if "useLabel" in binding:
            data["uses"].add(binding["useLabel"]["value"])
        if "description" in binding and not data["description_zh"]:
            data["description_zh"] = binding["description"]["value"]

    # set → list
    data["inventors"] = sorted(data["inventors"])
    data["uses"] = sorted(data["uses"])

    return data


def format_metadata_section(data: dict, zh_name: str, en_name: str, qid: str) -> str:
    """
    将查询结果格式化为 Markdown "基本信息" 章节。
    """
    lines = [
        "",
        "## 基本信息 (Structured Data from Wikidata)",
        "",
        f"| 属性 | 值 |",
        f"|------|-----|",
        f"| **中文名** | {zh_name} |",
        f"| **英文名** | {en_name} |",
    ]

    if data.get("formula"):
        lines.append(f"| **分子式** | {data['formula']} |")
    if data.get("cas"):
        lines.append(f"| **CAS号** | {data['cas']} |")
    if data.get("discovery_date"):
        lines.append(f"| **发现/发明年份** | {data['discovery_date']} |")
    if data.get("inventors"):
        lines.append(f"| **发明者/发现者** | {', '.join(data['inventors'])} |")
    if data.get("uses"):
        # 限制显示数量
        uses = data["uses"][:8]
        lines.append(f"| **用途** | {', '.join(uses)} |")
    if data.get("description_zh"):
        lines.append(f"| **中文描述** | {data['description_zh']} |")

    lines.append(f"| **Wikidata ID** | [{qid}](https://www.wikidata.org/wiki/{qid}) |")
    lines.append("")

    return "\n".join(lines)


def inject_metadata_into_md(filepath: str, metadata_section: str):
    """
    将结构化数据注入到 .md 文件中（在摘要章节之前插入）。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 找到 "## 摘要" 位置，在其前面插入
    marker = "## 摘要"
    if marker in content:
        content = content.replace(marker, metadata_section + "\n" + marker, 1)
    else:
        # 找到第一个 "---" 后插入
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[0] + "---" + "\n" + metadata_section + "\n---" + parts[2]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("Omphalina 知识库 — Wikidata 结构化数据补充")
    print("=" * 60)

    for filename, qid, zh_name, en_name in COMPOUND_WIKIDATA:
        filepath = os.path.join(COMPOUNDS_DIR, f"{filename}.md")

        if not os.path.exists(filepath):
            print(f"\n⚠️ 文件不存在，跳过: {filepath}")
            continue

        print(f"\n🔍 查询 Wikidata: {zh_name} ({qid})")
        data = query_compound_details(qid)

        if not data:
            print(f"  ⚠️ 无数据返回")
            continue

        # 打印查询结果摘要
        print(f"  分子式: {data.get('formula', 'N/A')}")
        print(f"  CAS号:  {data.get('cas', 'N/A')}")
        print(f"  发明年: {data.get('discovery_date', 'N/A')}")
        print(f"  发明者: {', '.join(data.get('inventors', [])) or 'N/A'}")
        print(f"  用途数: {len(data.get('uses', []))}")

        # 格式化并注入
        metadata_md = format_metadata_section(data, zh_name, en_name, qid)
        inject_metadata_into_md(filepath, metadata_md)
        print(f"  ✅ 已注入结构化数据到: {filename}.md")

    print("\n" + "=" * 60)
    print("Wikidata 补充完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
