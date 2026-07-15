"""Cross-source dedup + persistent seen-cache so weekly runs only report new papers."""
import json
import os
import re
from datetime import datetime, timezone


def normalize_title(title):
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"[^a-z0-9一-鿿]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def merge_duplicates(records):
    """Merge records referring to the same paper (matched by normalized title),
    combining which keywords/sources found it and preferring the entry with
    the most complete metadata (abstract, DOI)."""
    by_title = {}
    for r in records:
        key = normalize_title(r.get("title"))
        if not key:
            continue
        if key not in by_title:
            r = dict(r)
            r["matched_keywords"] = {r.pop("matched_keyword")}
            r["sources"] = {r.pop("source")}
            by_title[key] = r
        else:
            existing = by_title[key]
            existing["matched_keywords"].add(r.get("matched_keyword"))
            existing["sources"].add(r.get("source"))
            if not existing.get("abstract") and r.get("abstract"):
                existing["abstract"] = r.get("abstract")
            if not existing.get("doi") and r.get("doi"):
                existing["doi"] = r.get("doi")
            if not existing.get("url") and r.get("url"):
                existing["url"] = r.get("url")
            if not existing.get("oa_pdf_url") and r.get("oa_pdf_url"):
                existing["oa_pdf_url"] = r.get("oa_pdf_url")
    merged = []
    for rec in by_title.values():
        rec["matched_keywords"] = sorted(rec["matched_keywords"])
        rec["sources"] = sorted(rec["sources"])
        merged.append(rec)
    return merged


def filter_unseen(records, cache):
    """Drop records whose normalized title is already in the seen-cache."""
    return [r for r in records if normalize_title(r.get("title")) not in cache]


def select_diverse_top_n(records, n):
    """Pick up to n records, newest year first, preferring one per distinct
    venue before allowing a second paper from the same venue."""
    records_sorted = sorted(records, key=lambda r: r.get("year") or 0, reverse=True)
    selected, leftovers, used_venues = [], [], set()
    for r in records_sorted:
        if len(selected) >= n:
            break
        v = r.get("venue")
        if v not in used_venues:
            selected.append(r)
            used_venues.add(v)
        else:
            leftovers.append(r)
    for r in leftovers:
        if len(selected) >= n:
            break
        selected.append(r)
    return selected


def load_cache(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, cache):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def split_new_and_update_cache(records, cache):
    """Return (new_records, updated_cache). `records` must already be
    title-deduplicated via merge_duplicates()."""
    new_records = []
    now = datetime.now(timezone.utc).isoformat()
    for rec in records:
        key = normalize_title(rec.get("title"))
        if not key:
            continue
        if key not in cache:
            new_records.append(rec)
            cache[key] = {
                "title": rec.get("title"),
                "venue": rec.get("venue"),
                "year": rec.get("year"),
                "first_seen": now,
            }
    return new_records, cache
