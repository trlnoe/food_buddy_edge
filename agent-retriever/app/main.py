import time
from fastapi import FastAPI
from .schemas import RetrieveRequest
from .vector_store import RestaurantStore

app = FastAPI(title="Food Buddy Retriever", version="0.1.0")
store = RestaurantStore()

@app.get("/health")
def health():
    return {"status": "ok", "index_size": len(store.store.items), "mode": store.mode}

@app.post("/retrieve")
def retrieve(request: RetrieveRequest):
    started = time.perf_counter()
    results = store.query(request.query, request.top_k)
    if not results:
        return {"success": False, "error_code": "NO_RESULTS", "error_message": "No matching restaurants found.", "data": None}
    return {"success": True, "error_code": None, "error_message": None,
            "data": {"results": results, "latency_ms": round((time.perf_counter()-started)*1000, 2)}}
