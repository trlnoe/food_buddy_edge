import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .llm_engine import LocalLlmEngine
from .logic import select_restaurants
from .schemas import ReasonRequest

engine = LocalLlmEngine()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine.load()
    yield

app = FastAPI(title="Food Buddy Reasoner", version="0.3.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "engine": "llama_cpp" if engine.available else "deterministic_fallback",
        "model_loaded": engine.available,
        "model_error": engine.error,
    }

@app.post("/reason")
def reason(request: ReasonRequest):
    started = time.perf_counter()

    if os.getenv("FORCE_MALFORMED") == "1":
        return {
            "success": False,
            "error_code": "MALFORMED_OUTPUT",
            "error_message": "Forced malformed LLM output for fault demo.",
            "data": None,
        }

    data = select_restaurants(
        request.query, request.candidates, request.current_time
    )
    eligible_ids = set(data["chosen_ids"])
    eligible = [item for item in request.candidates if item["id"] in eligible_ids]

    if engine.available and eligible:
        try:
            data["answer_text"] = engine.generate(
                request.query, eligible, request.current_time
            )
            data["tokens_generated"] = len(data["answer_text"].split())
            data["llm_used"] = True
        except Exception as exc:
            data["llm_used"] = False
            data["llm_error"] = str(exc)
    else:
        data["llm_used"] = False

    return {
        "success": True,
        "error_code": None,
        "error_message": None,
        "data": data,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }
