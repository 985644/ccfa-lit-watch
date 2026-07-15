"""Download PDFs for papers that Semantic Scholar reports a legitimate open-access
copy for (oa_pdf_url, sourced from Unpaywall-style OA metadata). Never attempts to
fetch anything behind a publisher paywall or via unauthorized-access routes;
papers without a known OA copy are simply left to the "missing" list."""
import os
import re
import requests

_NO_PROXY = {"http": None, "https": None}


def _safe_filename(title, max_len=120):
    name = re.sub(r"[^\w\s-]", "", title or "untitled").strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] or "untitled"


def fetch_pdfs(records, pdf_dir):
    """For each record with an oa_pdf_url, try to download it as a real PDF.
    Returns (downloaded, missing) where each is a list of record dicts;
    downloaded records get a 'pdf_path' key added."""
    os.makedirs(pdf_dir, exist_ok=True)
    downloaded, missing = [], []

    for r in records:
        url = r.get("oa_pdf_url")
        if not url:
            missing.append(r)
            continue
        try:
            resp = requests.get(url, timeout=30, proxies=_NO_PROXY,
                                 headers={"User-Agent": "Mozilla/5.0 (literature-watch script)"})
            content_type = resp.headers.get("Content-Type", "")
            is_pdf = resp.status_code == 200 and (
                "pdf" in content_type.lower() or resp.content[:5] == b"%PDF-"
            )
            if not is_pdf:
                print(f"  [pdf] not a real PDF, skipping: {r.get('title')} ({url})")
                missing.append(r)
                continue
            fname = _safe_filename(r.get("title")) + ".pdf"
            path = os.path.join(pdf_dir, fname)
            with open(path, "wb") as f:
                f.write(resp.content)
            r = dict(r)
            r["pdf_path"] = path
            downloaded.append(r)
            print(f"  [pdf] downloaded: {fname}")
        except requests.exceptions.RequestException as e:
            print(f"  [pdf] failed to fetch {r.get('title')}: {e}")
            missing.append(r)

    return downloaded, missing
