#!/usr/bin/env python3
"""
Omphalina 知识库 — Wikipedia 全景知识拉取脚本

从 Wikipedia 英文版和中文版拉取化合物完整条目，
按章节重组为 Markdown 格式，存入 encyclopedia/compounds/。
同时拉取独立历史专题条目和关键人物传记。
"""

import os
import json
import time
from datetime import datetime

import wikipediaapi

# ============================================================
# 配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOUNDS_DIR = os.path.join(BASE_DIR, "encyclopedia", "compounds")
TOPICS_DIR = os.path.join(BASE_DIR, "encyclopedia", "topics")
PEOPLE_DIR = os.path.join(BASE_DIR, "encyclopedia", "people")
METADATA_PATH = os.path.join(BASE_DIR, "encyclopedia", "metadata.json")

USER_AGENT = "OmphalinaKnowledgeBase/1.0 (hackathon-project)"

# 代理配置（如需代理请设置 HTTP_PROXY / HTTPS_PROXY 环境变量）
PROXY = os.environ.get("HTTP_PROXY", os.environ.get("HTTPS_PROXY", ""))

# 7 个 MVP 化合物：(文件名, 英文 Wikipedia 标题, 中文 Wikipedia 标题)
COMPOUNDS = [
    ("aspirin",             "Aspirin",                  "阿司匹林"),
    ("synthetic_ammonia",   "Haber process",            "哈柏法"),
    ("plastics",            "Plastic",                  "塑料"),
    ("ddt",                 "DDT",                      "滴滴涕"),
    ("cfc",                 "Chlorofluorocarbon",       "氯氟烃"),
    ("penicillin",          "Penicillin",               "青霉素"),
    ("msg",                 "Monosodium glutamate",     "味精"),
]

# 独立历史专题条目
TOPICS = [
    ("history_of_aspirin",      "History of aspirin",       None),
    ("history_of_penicillin",   "History of penicillin",    None),
    ("silent_spring",           "Silent Spring",            "寂静的春天"),
    ("montreal_protocol",       "Montreal Protocol",        "蒙特利尔议定书"),
    ("haber_process_history",   "Fritz Haber",              "弗里茨·哈伯"),
]

# 关键人物传记
PEOPLE = [
    ("fritz_haber",         "Fritz Haber",              "弗里茨·哈伯"),
    ("rachel_carson",       "Rachel Carson",            "蕾切尔·卡森"),
    ("alexander_fleming",   "Alexander Fleming",        "亚历山大·弗莱明"),
    ("thomas_midgley",      "Thomas Midgley Jr.",       "小托马斯·米奇利"),
    ("paul_mueller",        "Paul Hermann Müller",      None),
    ("kikunae_ikeda",       "Kikunae Ikeda",            "池田菊苗"),
    ("felix_hoffmann",      "Felix Hoffmann",           None),
    ("carl_bosch",          "Carl Bosch",               "卡尔·博施"),
]

# ============================================================
# 工具函数
# ============================================================

def create_wiki(lang: str) -> wikipediaapi.Wikipedia:
    """创建指定语言的 Wikipedia API 客户端（通过代理）"""
    wiki = wikipediaapi.Wikipedia(
        user_agent=USER_AGENT,
        language=lang,
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        proxies={
            "http": PROXY,
            "https": PROXY,
        },
    )
    return wiki


def extract_sections_recursive(sections, level=2) -> str:
    """递归提取所有子章节，转换为 Markdown 格式"""
    md = ""
    for s in sections:
        # 跳过参考文献、外部链接等非内容章节
        skip_titles = {
            "References", "External links", "See also", "Further reading",
            "Notes", "Bibliography", "Sources", "Footnotes",
            "参考文献", "外部链接", "参见", "延伸阅读", "注释", "参考资料",
        }
        if s.title in skip_titles:
            continue

        heading = "#" * level
        md += f"\n{heading} {s.title}\n\n"
        if s.text.strip():
            md += s.text.strip() + "\n"
        # 递归子章节
        if s.sections:
            md += extract_sections_recursive(s.sections, level=level + 1)
    return md


def fetch_article(wiki, title: str) -> dict | None:
    """
    拉取单篇 Wikipedia 文章，返回结构化数据。
    返回 None 如果文章不存在。
    """
    page = wiki.page(title)
    if not page.exists():
        print(f"  ⚠️ 文章不存在: {title}")
        return None

    return {
        "title": page.title,
        "summary": page.summary,
        "full_url": page.fullurl,
        "sections_md": extract_sections_recursive(page.sections),
        "text_length": len(page.text),
    }


def build_compound_md(filename: str, en_title: str, zh_title: str | None,
                      wiki_en, wiki_zh) -> tuple[str, dict]:
    """
    构建一个化合物的完整 Markdown 百科条目。
    返回 (markdown_text, metadata_dict)。
    """
    print(f"\n📖 拉取化合物: {en_title}")

    # 拉取英文
    en_data = fetch_article(wiki_en, en_title)
    if not en_data:
        return "", {}

    # 拉取中文
    zh_data = None
    if zh_title:
        zh_data = fetch_article(wiki_zh, zh_title)

    # 组装 Markdown
    display_name_zh = zh_title or en_title
    md = f"# {display_name_zh} ({en_title})\n\n"
    md += f"> 来源: Wikipedia EN + ZH | 拉取日期: {datetime.now().strftime('%Y-%m-%d')}\n"
    md += f"> EN: {en_data['full_url']}\n"
    if zh_data:
        md += f"> ZH: {zh_data['full_url']}\n"
    md += "\n---\n\n"

    # 摘要
    md += "## 摘要 (Summary)\n\n"
    md += f"**English:**\n{en_data['summary']}\n\n"
    if zh_data:
        md += f"**中文:**\n{zh_data['summary']}\n\n"

    # 英文正文（按章节）
    md += "---\n\n"
    md += "## 英文 Wikipedia 全文\n"
    md += en_data["sections_md"]

    # 中文正文（补充）
    if zh_data and zh_data["sections_md"].strip():
        md += "\n---\n\n"
        md += "## 中文 Wikipedia 补充内容\n"
        md += zh_data["sections_md"]

    # 元数据
    meta = {
        "filename": filename,
        "en_title": en_title,
        "zh_title": zh_title,
        "en_url": en_data["full_url"],
        "zh_url": zh_data["full_url"] if zh_data else None,
        "en_chars": en_data["text_length"],
        "zh_chars": zh_data["text_length"] if zh_data else 0,
        "total_chars": en_data["text_length"] + (zh_data["text_length"] if zh_data else 0),
        "estimated_tokens": int((en_data["text_length"] + (zh_data["text_length"] if zh_data else 0)) * 0.35),
        "fetched_at": datetime.now().isoformat(),
    }

    return md, meta


def build_article_md(en_title: str, zh_title: str | None,
                     wiki_en, wiki_zh, category: str) -> tuple[str, dict]:
    """
    构建专题/人物条目的 Markdown。
    """
    print(f"\n📖 拉取{category}: {en_title}")

    en_data = fetch_article(wiki_en, en_title)
    if not en_data:
        return "", {}

    zh_data = None
    if zh_title:
        zh_data = fetch_article(wiki_zh, zh_title)

    display_name = zh_title or en_title
    md = f"# {display_name} ({en_title})\n\n"
    md += f"> 来源: Wikipedia | 类别: {category} | 拉取日期: {datetime.now().strftime('%Y-%m-%d')}\n"
    md += f"> EN: {en_data['full_url']}\n"
    if zh_data:
        md += f"> ZH: {zh_data['full_url']}\n"
    md += "\n---\n\n"

    md += "## 摘要\n\n"
    md += f"{en_data['summary']}\n\n"
    if zh_data:
        md += f"**中文摘要:**\n{zh_data['summary']}\n\n"

    md += "---\n\n"
    md += "## 英文全文\n"
    md += en_data["sections_md"]

    if zh_data and zh_data["sections_md"].strip():
        md += "\n---\n\n"
        md += "## 中文补充\n"
        md += zh_data["sections_md"]

    meta = {
        "en_title": en_title,
        "zh_title": zh_title,
        "en_url": en_data["full_url"],
        "zh_url": zh_data["full_url"] if zh_data else None,
        "en_chars": en_data["text_length"],
        "zh_chars": zh_data["text_length"] if zh_data else 0,
        "total_chars": en_data["text_length"] + (zh_data["text_length"] if zh_data else 0),
        "estimated_tokens": int((en_data["text_length"] + (zh_data["text_length"] if zh_data else 0)) * 0.35),
        "fetched_at": datetime.now().isoformat(),
        "category": category,
    }

    return md, meta


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("Omphalina 知识库 — Wikipedia 全景拉取")
    print("=" * 60)

    wiki_en = create_wiki("en")
    wiki_zh = create_wiki("zh")

    all_metadata = {
        "project": "Omphalina",
        "description": "化合物全景知识库 — 第一层百科数据",
        "generated_at": datetime.now().isoformat(),
        "compounds": {},
        "topics": {},
        "people": {},
        "totals": {},
    }

    total_chars = 0
    total_tokens = 0

    # --- 拉取 7 个化合物 ---
    print("\n" + "=" * 40)
    print("第一步：拉取 7 个化合物百科条目")
    print("=" * 40)

    for filename, en_title, zh_title in COMPOUNDS:
        md, meta = build_compound_md(filename, en_title, zh_title, wiki_en, wiki_zh)
        if md:
            filepath = os.path.join(COMPOUNDS_DIR, f"{filename}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  ✅ 已保存: {filepath}")
            print(f"     字符数: {meta['total_chars']:,} | 估算 tokens: {meta['estimated_tokens']:,}")
            all_metadata["compounds"][filename] = meta
            total_chars += meta["total_chars"]
            total_tokens += meta["estimated_tokens"]
        time.sleep(1)  # 礼貌延迟，避免请求过快

    # --- 拉取专题条目 ---
    print("\n" + "=" * 40)
    print("第二步：拉取专题补充条目")
    print("=" * 40)

    for filename, en_title, zh_title in TOPICS:
        md, meta = build_article_md(en_title, zh_title, wiki_en, wiki_zh, "专题")
        if md:
            filepath = os.path.join(TOPICS_DIR, f"{filename}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  ✅ 已保存: {filepath}")
            all_metadata["topics"][filename] = meta
            total_chars += meta.get("total_chars", 0)
            total_tokens += meta.get("estimated_tokens", 0)
        time.sleep(1)

    # --- 拉取人物传记 ---
    print("\n" + "=" * 40)
    print("第三步：拉取关键人物传记")
    print("=" * 40)

    for filename, en_title, zh_title in PEOPLE:
        md, meta = build_article_md(en_title, zh_title, wiki_en, wiki_zh, "人物传记")
        if md:
            filepath = os.path.join(PEOPLE_DIR, f"{filename}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  ✅ 已保存: {filepath}")
            all_metadata["people"][filename] = meta
            total_chars += meta.get("total_chars", 0)
            total_tokens += meta.get("estimated_tokens", 0)
        time.sleep(1)

    # --- 汇总统计 ---
    all_metadata["totals"] = {
        "total_chars": total_chars,
        "total_estimated_tokens": total_tokens,
        "gemini_context_usage_pct": round(total_tokens / 1_000_000 * 100, 1),
        "compound_count": len(all_metadata["compounds"]),
        "topic_count": len(all_metadata["topics"]),
        "people_count": len(all_metadata["people"]),
    }

    # 保存元数据
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    # 打印汇总
    print("\n" + "=" * 60)
    print("📊 拉取完成！汇总统计:")
    print("=" * 60)
    print(f"  化合物条目: {all_metadata['totals']['compound_count']}")
    print(f"  专题条目:   {all_metadata['totals']['topic_count']}")
    print(f"  人物传记:   {all_metadata['totals']['people_count']}")
    print(f"  总字符数:   {total_chars:,}")
    print(f"  估算 Token: {total_tokens:,}")
    print(f"  Gemini 上下文占比: ~{all_metadata['totals']['gemini_context_usage_pct']}%")
    print(f"\n  元数据已保存: {METADATA_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
