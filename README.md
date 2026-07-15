# CCF-A Literature Watch

Searches Semantic Scholar + DBLP for recent papers in a fixed set of CCF-A
journals/conferences (categories E/H/J — data mining, AI, interdisciplinary),
matched against a fixed keyword list drawn from the user's active graph
fraud/anomaly detection research (see `config.py`). Deduplicates against
`seen_cache.json` so repeated runs only surface genuinely new papers.

## Usage

```
python main.py                              # fixed weekly keyword list -> reports/
python main.py --keywords "kw1, kw2"         # manual custom keywords -> output/
python main.py --keywords "..." --peek       # don't mark results as seen
```

## Weekly automated run (cloud routine)

Every Monday 9am Asia/Shanghai, a scheduled cloud agent:
1. Runs `python main.py` (fixed keyword mode) to produce a new file under `reports/`.
2. Commits and pushes the new report + updated `seen_cache.json` back to this repo.
3. Uploads a copy of the same report to the user's connected Google Drive.

A separate Windows Task Scheduler job on the user's local machine (not part of
this repo) pulls the latest commit weekly and converts new `reports/*.md`
files to `.docx`/`.pdf` for local reading.

## Files

- `config.py` — venue whitelist + alias map, fixed keyword list, min year
- `s2_search.py` / `dblp_search.py` — per-source search + venue filtering
- `aggregate.py` — cross-source title dedup + persistent seen-cache
- `digest.py` — renders new records into a markdown report grouped by venue
- `main.py` — CLI entry point
