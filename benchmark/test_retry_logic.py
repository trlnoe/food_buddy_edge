import asyncio
import httpx
import json

API_URL = "http://localhost:8885/reason"

payload = {
    "query": "good seafood",
    "candidates": [
        {"id": "c1", "name": "Ganh Hao", "area": "Front Beach", "cuisine_type": ["seafood"], "specialties": ["crab"], "rating": 4.5, "price_min": 100000, "price_max": 300000, "open_time": "09:00", "close_time": "23:00"}
    ],
    "current_time": "12:00"
}

async def test_retry():
    print("Sending request to Reasoner (with FORCE_MALFORMED=1 in env)...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json=payload, timeout=30.0)
            data = response.json()
            print("Response:", json.dumps(data, indent=2))
            if data.get("attempts") == 2 and data.get("success"):
                print("✅ Test PASSED: The Reasoner successfully retried and recovered on the 2nd attempt.")
            else:
                print("❌ Test FAILED: Did not recover as expected or didn't take 2 attempts.")
        except Exception as e:
            print(f"❌ Test FAILED with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_retry())
