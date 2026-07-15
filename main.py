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
from datetime import datetime

import config
import s2_search
import dblp_search
from aggregate import load_cache, save_cache, merge_duplicates, split_new_and_update_cache
from digest import render_markdown


def main():
    parser = argparse.ArgumentParser(description="CCF-A venue-scoped literature watch")
    parser.add_argument("--keywords", type=str, default=None,
                         help="Comma-separated custom keywords. Omit to use the fixed weekly list.")
    parser.add_argument("--min-year", type=int, default=config.MIN_YEAR)
    parser.add_argument("--peek", action="store_true",
                         help="Don't mark results as seen (won't be suppressed on the next run).")
    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        mode_label = "manual"
    else:
        keywords = config.FIXED_KEYWORDS
        mode_label = "weekly-fixed"

    print(f"Mode: {mode_label} | keywords: {keywords} | min_year: {args.min_year}")

    s2_results = s2_search.search_keywords(keywords, min_year=args.min_year)
    dblp_results = dblp_search.search_keywords(keywords, min_year=args.min_year)

    merged = merge_duplicates(s2_results + dblp_results)
    print(f"Merged unique papers across sources: {len(merged)}")

    cache = load_cache(config.CACHE_PATH)
    new_records, updated_cache = split_new_and_update_cache(merged, cache)
    print(f"New (not previously seen): {len(new_records)}")

    if not args.peek:
        save_cache(config.CACHE_PATH, updated_cache)
    else:
        print("--peek set: cache not updated, these results may reappear next run.")

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"CCF-A 文献监控周报 ({mode_label})" if mode_label == "weekly-fixed" else "CCF-A 文献检索结果 (手动)"
    md = render_markdown(new_records, title, run_date, keywords)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    fname = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{mode_label}.md"
    out_path = os.path.join(config.OUTPUT_DIR, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nDigest written to: {out_path}\n")
    print(md)


if __name__ == "__main__":
    main()
