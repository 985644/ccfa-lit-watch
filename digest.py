"""Render a list of new-paper records into a markdown digest, grouped by venue."""
from collections import defaultdict


def render_markdown(records, title, run_date, keywords):
    lines = [f"# {title}", "", f"运行时间: {run_date}", "", f"检索关键词: {', '.join(keywords)}", ""]

    if not records:
        lines.append("本次未发现符合范围的新文献。")
        return "\n".join(lines)

    lines.append(f"共发现 **{len(records)}** 篇新文献。")
    lines.append("")

    by_venue = defaultdict(list)
    for r in records:
        by_venue[r.get("venue", "Unknown")].append(r)

    for venue in sorted(by_venue.keys()):
        papers = by_venue[venue]
        lines.append(f"## {venue} ({len(papers)})")
        lines.append("")
        for p in sorted(papers, key=lambda x: (x.get("year") or 0), reverse=True):
            authors = ", ".join(p.get("authors") or []) or "作者未知"
            year = p.get("year") or "年份未知"
            kw = ", ".join(p.get("matched_keywords") or [])
            src = "/".join(p.get("sources") or [])
            lines.append(f"### {p.get('title')}")
            lines.append(f"- 作者: {authors}")
            lines.append(f"- 年份: {year} | 来源: {src} | 命中关键词: {kw}")
            if p.get("url"):
                lines.append(f"- 链接: {p.get('url')}")
            if p.get("doi"):
                lines.append(f"- DOI: {p.get('doi')}")
            if p.get("abstract"):
                abstract = p["abstract"].strip().replace("\n", " ")
                if len(abstract) > 400:
                    abstract = abstract[:400].rstrip() + "..."
                lines.append(f"- 摘要: {abstract}")
            lines.append("")

    return "\n".join(lines)
