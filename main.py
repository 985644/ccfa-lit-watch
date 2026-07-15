#!/usr/bin/env python
"""CCF-A literature watch entry point.

Weekly automated mode (fixed keywords from config.FIXED_KEYWORDS):
    python main.py

Manual mode (your own keywords, comma-separated):
    python main.py --keywords "graph rewiring, node-level gating"

Peek without marking results as seen (won't suppress them from a later run):
    python main.py --keywords "..." --peek
"""
import argparse
import os
from datetime import datetime, timezone

import config
import s2_search
import dblp_search
from aggregate import (
    load_cache, save_cache, merge_duplicates,
    filter_unseen, select_diverse_top_n, normalize_title,
)
from digest import render_markdown
from pdf_fetch import fetch_pdfs
from docgen import write_missing_pdf_docx


def search_one_keyword(keyword, min_year, cache, max_per_keyword, include_seen=False):
    """Search + merge + (optionally) drop already-seen + pick up to
    max_per_keyword, newest year first, preferring distinct venues."""
    try:
        s2_hits = s2_search.search_keyword(keyword, min_year=min_year)
    except Exception as e:
        print(f"  [S2] failed for '{keyword}': {e}")
        s2_hits = []
    try:
        dblp_hits = dblp_search.search_keyword(keyword, min_year=min_year)
    except Exception as e:
        print(f"  [DBLP] failed for '{keyword}': {e}")
        dblp_hits = []
    merged = merge_duplicates(s2_hits + dblp_hits)
    pool = merged if include_seen else filter_unseen(merged, cache)
    selected = select_diverse_top_n(pool, max_per_keyword)
    print(f"  -> {len(merged)} unique candidates, {len(pool)} in pool ({'seen included' if include_seen else 'unseen only'}), {len(selected)} selected")
    return selected


def main():
    parser = argparse.ArgumentParser(description="CCF-A venue-scoped literature watch")
    parser.add_argument("--keywords", type=str, default=None,
                         help="Comma-separated custom keywords. Omit to use the fixed weekly list.")
    parser.add_argument("--min-year", type=int, default=config.MIN_YEAR)
    parser.add_argument("--max-per-keyword", type=int, default=config.MAX_PER_KEYWORD)
    parser.add_argument("--peek", action="store_true",
                         help="Don't mark results as seen (won't be suppressed on the next run).")
    parser.add_argument("--include-seen", action="store_true",
                         help="Don't hide papers already in the seen-cache (useful for a one-off deep-dive search).")
    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        mode_label = "manual"
    else:
        keywords = config.FIXED_KEYWORDS
        mode_label = "weekly-fixed"

    print(f"Mode: {mode_label} | keywords: {keywords} | min_year: {args.min_year} | max_per_keyword: {args.max_per_keyword}")

    cache = load_cache(config.CACHE_PATH)

    all_selected = []
    for kw in keywords:
        print(f"[keyword] {kw}")
        all_selected.extend(search_one_keyword(kw, args.min_year, cache, args.max_per_keyword, include_seen=args.include_seen))

    print(f"Total selected across all keywords: {len(all_selected)}")

    if not args.peek:
        now = datetime.now(timezone.utc).isoformat()
        for r in all_selected:
            key = normalize_title(r.get("title"))
            if key:
                cache[key] = {
                    "title": r.get("title"),
                    "venue": r.get("venue"),
                    "year": r.get("year"),
                    "first_seen": now,
                }
        save_cache(config.CACHE_PATH, cache)
    else:
        print("--peek set: cache not updated, these results may reappear next run.")

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"CCF-A 文献监控周报 ({mode_label})" if mode_label == "weekly-fixed" else "CCF-A 文献检索结果 (手动)"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_dir = config.PDF_DIR  # flat folder, all runs accumulate PDFs directly here
    downloaded, missing = fetch_pdfs(all_selected, pdf_dir)
    print(f"PDFs downloaded (open-access only): {len(downloaded)} | no OA copy available: {len(missing)}")

    missing_docx_path = None
    if missing:
        missing_md_path = os.path.join(pdf_dir, f"missing_pdfs_{stamp}_{mode_label}.md")
        missing_docx_path = os.path.join(pdf_dir, f"missing_pdfs_{stamp}_{mode_label}.docx")
        write_missing_pdf_docx(missing, missing_md_path, missing_docx_path, run_date)
        print(f"Missing-PDF citation list written to: {missing_docx_path}")

    md = render_markdown(downloaded + missing, title, run_date, keywords, pdf_dir=pdf_dir if all_selected else None)

    out_dir = config.WEEKLY_OUTPUT_DIR if mode_label == "weekly-fixed" else config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    fname = stamp + f"_{mode_label}.md"
    out_path = os.path.join(out_dir, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nDigest written to: {out_path}\n")
    print(md)


if __name__ == "__main__":
    main()
