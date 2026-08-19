"""Optional semantic index builder. Requires network the first time to fetch MiniLM."""
import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

root = Path(__file__).resolve().parents[1]
items = json.loads((root / "data/restaurants.json").read_text())
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=str(root / "chroma_db"))
client.delete_collection("restaurants") if "restaurants" in [c.name for c in client.list_collections()] else None
collection = client.create_collection("restaurants", metadata={"hnsw:space": "cosine"})
docs = [f"{x['name']}. {x['area']}. {', '.join(x['cuisine_type'])}. Specialties: {', '.join(x['specialties'])}. {x['description']}" for x in items]
collection.add(ids=[x["id"] for x in items], documents=docs, embeddings=model.encode(docs).tolist(), metadatas=[{"id": x["id"]} for x in items])
print(f"Indexed {len(items)} restaurants in {root / 'chroma_db'}")
