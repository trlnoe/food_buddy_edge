import json

SYSTEM_PROMPT = """You are a friendly local food assistant for tourists visiting Vung Tau, Vietnam.
Recommend ONLY restaurants from the provided candidate list. Never invent a restaurant.
Write a short natural English answer (2–3 sentences). For every recommendation, mention
the price range and one specialty. If the list is empty, honestly say no suitable open
restaurant was found. Return plain text only, not JSON and no markdown."""

def user_prompt(query: str, candidates: list[dict], current_time: str) -> str:
    return (
        f"User query: {query}\n"
        f"Current local time: {current_time}\n"
        f"Eligible restaurants only:\n{json.dumps(candidates, ensure_ascii=False)}"
    )
