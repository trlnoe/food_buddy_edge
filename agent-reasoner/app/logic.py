import re
from datetime import datetime

def is_open(open_time: str, close_time: str, current: str) -> bool:
    start = datetime.strptime(open_time, "%H:%M").time()
    end = datetime.strptime(close_time, "%H:%M").time()
    now = datetime.strptime(current, "%H:%M").time()
    return start <= now <= end if start <= end else now >= start or now <= end

def select_restaurants(query: str, candidates: list[dict], current_time: str) -> dict:
    query_lower = query.lower()
    chosen, excluded, reasons = [], [], {}
    budget_match = re.search(r"(?:under|below|less than)\s*(\d+)\s*k", query_lower)
    budget = int(budget_match.group(1)) * 1000 if budget_match else None
    for candidate in candidates:
        if not is_open(candidate["open_time"], candidate["close_time"], current_time):
            excluded.append(candidate["id"]); reasons[candidate["id"]] = f"Closed at {current_time} (hours {candidate['open_time']}-{candidate['close_time']})."
        elif budget is not None and candidate["price_min"] > budget:
            excluded.append(candidate["id"]); reasons[candidate["id"]] = f"Starts at {candidate['price_min']:,} VND, above the stated budget."
        elif len(chosen) < 50:
            chosen.append(candidate)
    if not chosen:
        answer = "I couldn't find an open restaurant matching those conditions right now. Please try a different time or relax the budget."
    else:
        lines = [f"{x['name']} ({x['area']}) — {x['price_min']:,}-{x['price_max']:,} VND; try the {x['specialties'][0] if x['specialties'] else 'house special'}." for x in chosen]
        answer = " ".join(["Here are my best matches:", *lines])
    return {"answer_text": answer, "chosen_ids": [x["id"] for x in chosen], "excluded_ids": excluded, "exclusion_reason": reasons, "tokens_generated": len(answer.split())}
