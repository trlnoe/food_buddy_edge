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

from pydantic import ValidationError
from .schemas import ReasonRequest, ReasonOutput

@app.post("/reason")
def reason(request: ReasonRequest):
    started = time.perf_counter()
    last_error = None

    for attempt in range(2):
        corrupt = (os.getenv("FORCE_MALFORMED") == "1") and (attempt == 0)

        data = select_restaurants(
            request.query, request.candidates, request.current_time
        )
        eligible_ids = set(data["chosen_ids"])
        eligible = [item for item in request.candidates if item["id"] in eligible_ids]

        if engine.available and eligible and not corrupt:
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

        if corrupt:
            # Artificially fail schema validation (ReasonOutput requires min_length=1)
            data["answer_text"] = ""

        try:
            ReasonOutput(**data) # validate the schema
            return {
                "success": True,
                "error_code": None,
                "error_message": None,
                "data": data,
                "attempts": attempt + 1,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        except ValidationError as e:
            last_error = str(e)
            continue # Try again on the next attempt

    # If we get here, both attempts failed
    return {
        "success": False,
        "error_code": "MALFORMED_OUTPUT",
        "error_message": "Forced malformed LLM output for fault demo." if os.getenv("FORCE_MALFORMED") == "1" else f"Validation failed: {last_error}",
        "data": None,
        "attempts": 2,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }
