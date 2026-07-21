"""Semantic Scholar Graph API search, filtered to the CCF-A venue whitelist."""
import time
import requests

from config import S2_API_BASE, VENUES, MIN_YEAR

FIELDS = "title,authors,venue,year,url,abstract,externalIds,publicationDate,openAccessPdf"

# Flatten venue -> aliases into a single list of (canonical_name, alias_lower) pairs
_ALIAS_INDEX = [
    (canonical, alias.strip().lower())
    for canonical, aliases in VENUES.items()
    for alias in aliases
]


def _match_venue(venue_str):
    """Return the canonical venue name if venue_str matches any known alias, else None."""
    if not venue_str:
        return None
    v = venue_str.lower()
    for canonical, alias in _ALIAS_INDEX:
        # Avoid treating journals whose names merely contain "Artif. Intell."
        # (notably Engineering Applications of AI) as the CCF-A AIJ venue.
        if canonical == "AIJ" and alias == "artif. intell." and v != alias:
            continue
        if alias in v:
            return canonical
    return None


_NO_PROXY = {"http": None, "https": None}


def _get_with_retry(url, params, max_retries=5):
    delay = 2.0
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, timeout=20, proxies=_NO_PROXY)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = float(resp.headers.get("Retry-After", delay))
            print(f"  [S2] 429 rate limited, waiting {wait:.0f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            delay *= 2
            continue
        resp.raise_for_status()
    raise RuntimeError(f"S2 request failed after {max_retries} retries: {url} {params}")


def search_keyword(keyword, min_year=MIN_YEAR):
    """Query Semantic Scholar for `keyword`, return list of paper dicts matching the venue whitelist."""
    params = {
        "query": keyword,
        "fields": FIELDS,
        "limit": 30,
        "year": f"{min_year}-",
    }
    data = _get_with_retry(S2_API_BASE, params)
    results = []
    for paper in data.get("data", []):
        canonical = _match_venue(paper.get("venue"))
        if not canonical:
            continue
        authors = [a.get("name") for a in (paper.get("authors") or [])]
        results.append({
            "source": "semantic_scholar",
            "paper_id": paper.get("paperId"),
            "doi": (paper.get("externalIds") or {}).get("DOI"),
            "title": paper.get("title"),
            "authors": authors,
            "venue": canonical,
            "venue_raw": paper.get("venue"),
            "year": paper.get("year"),
            "publication_date": paper.get("publicationDate"),
            "url": paper.get("url"),
            "abstract": paper.get("abstract"),
            "matched_keyword": keyword,
            "oa_pdf_url": (paper.get("openAccessPdf") or {}).get("url"),
        })
    # be polite to the shared unauthenticated rate-limit pool
    time.sleep(3.0)
    return results


def search_keywords(keywords, min_year=MIN_YEAR):
    all_results = []
    for kw in keywords:
        print(f"[S2] searching: {kw}")
        try:
            hits = search_keyword(kw, min_year=min_year)
        except Exception as e:
            print(f"  [S2] failed for '{kw}': {e}")
            continue
        print(f"  [S2] {len(hits)} venue-matched hits")
        all_results.extend(hits)
    return all_results
