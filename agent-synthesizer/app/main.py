import asyncio, os, time
from datetime import datetime
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Food Buddy Synthesizer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
RETRIEVER = os.getenv("RETRIEVER_URL", "http://retriever:8001")
REASONER = os.getenv("REASONER_URL", "http://reasoner:8002")
RTIMEOUT = float(os.getenv("RETRIEVER_TIMEOUT_SECONDS", "3"))
BTIMEOUT = float(os.getenv("REASONER_TIMEOUT_SECONDS", "20"))

class AskRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)

async def post_retry(client, url, payload, timeout):
    last = None
    for _ in range(2):
        try:
            response = await client.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json(), None
        except (httpx.HTTPError, ValueError) as exc:
            last = str(exc)
    return None, last

@app.get("/health")
async def health(): return {"status": "ok", "role": "orchestrator"}

@app.get("/status")
async def status():
    async with httpx.AsyncClient() as client:
        checks = await asyncio.gather(*[client.get(f"{u}/health", timeout=1.5) for u in (RETRIEVER, REASONER)], return_exceptions=True)
    return {"retriever": "ok" if not isinstance(checks[0], Exception) else "unavailable", "reasoner": "ok" if not isinstance(checks[1], Exception) else "unavailable"}

@app.post("/ask")
async def ask(request: AskRequest):
    started = time.perf_counter()
    async with httpx.AsyncClient() as client:
        retrieved, error = await post_retry(client, f"{RETRIEVER}/retrieve", {"query": request.query, "top_k": 5}, RTIMEOUT)
        if error:
            return failure("TIMEOUT", "Restaurant search is temporarily unavailable. Please try again shortly.", {"retriever":"timeout", "reasoner":"not_called"}, started)
        if not retrieved.get("success"):
            return failure(retrieved.get("error_code", "NO_RESULTS"), retrieved.get("error_message", "No restaurants found."), {"retriever":"error", "reasoner":"not_called"}, started)
        current = os.getenv("CURRENT_TIME_OVERRIDE") or datetime.now().strftime("%H:%M")
        reasoned, error = await post_retry(client, f"{REASONER}/reason", {"query":request.query, "candidates":retrieved["data"]["results"], "current_time":current}, BTIMEOUT)
        if error:
            return failure("TIMEOUT", "Restaurant advice is temporarily unavailable. Please try again shortly.", {"retriever":"ok", "reasoner":"timeout"}, started)
        if not reasoned.get("success"):
            return failure(reasoned.get("error_code", "MALFORMED_OUTPUT"), "Our local advisor returned an invalid answer; please retry.", {"retriever":"ok", "reasoner":"error"}, started)
    chosen_candidates = [r for r in retrieved["data"]["results"] if r["id"] in reasoned["data"]["chosen_ids"]]
    total = round((time.perf_counter()-started)*1000, 2)
    return {"success":True, "error_code":None, "error_message":None, "data":{"answer":reasoned["data"]["answer_text"], "chosen_ids":reasoned["data"]["chosen_ids"], "chosen_candidates": chosen_candidates, "agents_status":{"retriever":"ok","reasoner":"ok"}, "breakdown":{"retriever_ms":retrieved["data"]["latency_ms"],"reasoner_ms":reasoned["latency_ms"],"orchestration_overhead_ms":round(total-retrieved["data"]["latency_ms"]-reasoned["latency_ms"],2)}}, "total_latency_ms":total}

def failure(code, message, statuses, started):
    return {"success":False,"error_code":code,"error_message":message,"data":{"agents_status":statuses},"total_latency_ms":round((time.perf_counter()-started)*1000,2)}
