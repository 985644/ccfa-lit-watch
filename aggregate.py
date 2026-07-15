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
    merged = []
    for rec in by_title.values():
        rec["matched_keywords"] = sorted(rec["matched_keywords"])
        rec["sources"] = sorted(rec["sources"])
        merged.append(rec)
    return merged


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
