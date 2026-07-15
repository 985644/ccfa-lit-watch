# CCF-A literature watch: venue scope + fixed keyword list.
# Venue scope = CCF recommended list 2022, categories E (Databases/Data Mining/IR),
# H (Artificial Intelligence), J (Interdisciplinary) — the three starred in
# https://985644.github.io/ccfa/, matching the user's research direction.
# Each venue maps to a list of alias strings that might appear in the "venue"
# field returned by Semantic Scholar / DBLP, since neither source normalizes
# venue names to a single canonical form.

VENUES = {
    # --- E: Databases / Data Mining / Information Retrieval ---
    "TODS": ["ACM Transactions on Database Systems", "TODS"],
    "TOIS": ["ACM Transactions on Information Systems", "TOIS"],
    "TKDE": ["IEEE Transactions on Knowledge and Data Engineering", "TKDE"],
    "VLDB Journal": ["The VLDB Journal", "VLDB Journal"],
    "SIGMOD": ["SIGMOD", "International Conference on Management of Data"],
    "SIGKDD": ["KDD", "Knowledge Discovery and Data Mining"],
    "ICDE": ["ICDE", "International Conference on Data Engineering"],
    "SIGIR": ["SIGIR"],
    "VLDB": ["VLDB", "Very Large Data Bases"],
    # --- H: Artificial Intelligence ---
    "AIJ": ["Artificial Intelligence Journal", "Artif. Intell.", "AIJ"],
    "TPAMI": ["IEEE Transactions on Pattern Analysis and Machine Intelligence", "TPAMI"],
    "IJCV": ["International Journal of Computer Vision", "IJCV"],
    "JMLR": ["Journal of Machine Learning Research", "JMLR"],
    "AAAI": ["AAAI"],
    "NeurIPS": ["NeurIPS", "Neural Information Processing Systems", "NIPS"],
    "ACL": ["Annual Meeting of the Association for Computational Linguistics", " ACL"],
    "CVPR": ["CVPR", "Computer Vision and Pattern Recognition"],
    "ICCV": ["ICCV", "International Conference on Computer Vision"],
    "ICML": ["ICML", "International Conference on Machine Learning"],
    "IJCAI": ["IJCAI"],
    # --- J: Interdisciplinary / Comprehensive / Emerging ---
    "WWW": ["The Web Conference", "World Wide Web Conference", "WWW '", "TheWebConf"],
    "AAMAS": ["Autonomous Agents and Multiagent Systems", "AAMAS"],
}

# Fixed keyword set for the weekly automated run, drawn from the four active
# paper projects: FIGNN (interpretability), Fraud Channel (certified/path
# robustness), Few-shot OOD Fraud, and AGMF (heterophily + adaptive gating).
FIXED_KEYWORDS = [
    "graph fraud detection",
    "graph anomaly detection",
    "heterophilic graph neural network",
    "few-shot graph anomaly detection",
    "out-of-distribution graph generalization",
    "interpretable graph neural network fraud",
    "certified robust graph neural network",
    "adaptive propagation graph neural network",
]

# Only papers with a publication year at or after this are considered
# (keeps the query focused on genuinely recent work rather than the full
# citation history of each keyword).
MIN_YEAR = 2024

CACHE_PATH = "seen_cache.json"
OUTPUT_DIR = "output"

S2_API_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
DBLP_API_BASE = "https://dblp.org/search/publ/api"
