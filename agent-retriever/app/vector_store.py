import json
import re
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants.json"

def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))

import logging

CHROMA_DB_PATH = Path(__file__).resolve().parents[1] / "chroma_db"

class LexicalStore:
    """Portable lexical fallback; keyword-overlap scoring."""
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

class SemanticStore:
    """Semantic search using ChromaDB and sentence-transformers."""
    def __init__(self):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.items = {item["id"]: item for item in json.loads(DATA_PATH.read_text(encoding="utf-8"))}
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        self.collection = self.client.get_collection(name="restaurants")
        # Ensure we only load model if chroma collection was successfully loaded
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def query(self, query: str, top_k: int) -> list[dict]:
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        scored = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                item = self.items[doc_id]
                distance = results['distances'][0][i] if 'distances' in results and results['distances'] else 0
                # Pseudo score: Chroma cosine/L2 distance mapped to score + rating bias
                score = max(0, 1.0 - distance) + item["rating"] / 100
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [{**item, "score": round(score, 3)} for score, item in scored[:top_k]]

class RestaurantStore:
    """Facade that tries semantic search and falls back to lexical."""
    def __init__(self):
        self.mode = "lexical_fallback"
        self.store = self._try_load_semantic()

    def _try_load_semantic(self):
        if CHROMA_DB_PATH.exists() and any(CHROMA_DB_PATH.iterdir()):
            try:
                store = SemanticStore()
                self.mode = "semantic_chroma"
                logging.info("Successfully loaded SemanticStore with ChromaDB.")
                return store
            except Exception as e:
                logging.warning(f"Failed to load SemanticStore: {e}. Falling back to LexicalStore.")
        return LexicalStore()

    def query(self, query: str, top_k: int) -> list[dict]:
        return self.store.query(query, top_k)
