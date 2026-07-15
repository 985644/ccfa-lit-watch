"""Render the list of papers with no available open-access PDF into a .docx
citation list, via pandoc (already installed on this machine)."""
import subprocess


def write_missing_pdf_docx(records, md_path, docx_path, run_date):
    lines = [f"# 无法下载PDF的文献清单", "", f"生成时间: {run_date}", "",
             "以下文献没有公开可下载的开放获取(Open Access)版本"
             "(通常是被ACM/IEEE/Springer等出版商付费墙保护),"
             "本工作流不会尝试绕过付费墙下载，仅列出文献信息供你自行通过图书馆/机构订阅获取。",
             ""]
    for r in records:
        authors = ", ".join(r.get("authors") or []) or "作者未知"
        lines.append(f"## {r.get('title')}")
        lines.append(f"- 作者: {authors}")
        lines.append(f"- 年份: {r.get('year') or '未知'} | Venue: {r.get('venue')}")
        if r.get("doi"):
            lines.append(f"- DOI: {r.get('doi')}")
        if r.get("url"):
            lines.append(f"- 链接: {r.get('url')}")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    result = subprocess.run(["pandoc", md_path, "-o", docx_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed converting {md_path}: {result.stderr}")
    return docx_path
