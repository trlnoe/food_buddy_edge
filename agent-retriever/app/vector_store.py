import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants.json"

def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))

class RestaurantStore:
    """Portable lexical fallback; build_index.py can add Chroma for semantic search."""
    def __init__(self):
        self.items = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    def query(self, query: str, top_k: int) -> list[dict]:
        query_terms = _tokens(query)
        scored = []
        for item in self.items:
            text = " ".join([item["name"], item["area"], item["description"], *item["cuisine_type"], *item["specialties"]])
            terms = _tokens(text)
            overlap = len(query_terms & terms)
            # Retain a weak quality prior so queries with sparse wording are stable.
            score = overlap / max(1, len(query_terms)) + item["rating"] / 100
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [{**item, "score": round(score, 3)} for score, item in scored[:top_k] if score > 0.04]
