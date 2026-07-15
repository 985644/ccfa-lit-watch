"""DBLP publication search API, filtered to the CCF-A venue whitelist."""
import time
import requests

from config import DBLP_API_BASE, VENUES, MIN_YEAR

_ALIAS_INDEX = [
    (canonical, alias.strip().lower())
    for canonical, aliases in VENUES.items()
    for alias in aliases
]


def _match_venue(venue_str):
    if not venue_str:
        return None
    v = venue_str.lower()
    for canonical, alias in _ALIAS_INDEX:
        if alias in v:
            return canonical
    return None


def _as_list(x):
    """DBLP's JSON collapses single-item collections to a bare dict instead of a list."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _get_with_retry(url, params, max_retries=4):
    delay = 2.0
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=20, proxies={"http": None, "https": None})
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", delay))
                print(f"  [DBLP] 429 rate limited, waiting {wait:.0f}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                delay *= 2
                continue
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  [DBLP] connection error, retrying in {delay:.0f}s (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"DBLP request failed after {max_retries} retries: {url} {params}")


def search_keyword(keyword, min_year=MIN_YEAR, hits=100):
    params = {"q": keyword, "format": "json", "h": hits}
    data = _get_with_retry(params=params, url=DBLP_API_BASE)

    results = []
    hit_list = _as_list(data.get("result", {}).get("hits", {}).get("hit"))
    for hit in hit_list:
        info = hit.get("info", {})
        venue_raw = info.get("venue")
        canonical = _match_venue(venue_raw)
        if not canonical:
            continue
        try:
            year = int(info.get("year"))
        except (TypeError, ValueError):
            year = None
        if year is not None and year < min_year:
            continue
        authors = [a.get("text") if isinstance(a, dict) else a
                   for a in _as_list(info.get("authors", {}).get("author"))]
        results.append({
            "source": "dblp",
            "paper_id": info.get("key"),
            "doi": info.get("doi"),
            "title": info.get("title"),
            "authors": authors,
            "venue": canonical,
            "venue_raw": venue_raw,
            "year": year,
            "publication_date": None,
            "url": info.get("ee") or info.get("url"),
            "abstract": None,
            "matched_keyword": keyword,
        })
    time.sleep(1.5)
    return results


def search_keywords(keywords, min_year=MIN_YEAR):
    all_results = []
    for kw in keywords:
        print(f"[DBLP] searching: {kw}")
        try:
            hits = search_keyword(kw, min_year=min_year)
        except Exception as e:
            print(f"  [DBLP] failed for '{kw}': {e}")
            continue
        print(f"  [DBLP] {len(hits)} venue-matched hits")
        all_results.extend(hits)
    return all_results
