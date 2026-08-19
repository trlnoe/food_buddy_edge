import httpx
import time
import numpy as np
import json
import argparse
import asyncio

API_URL = "http://localhost:8887/ask"
TEST_QUERIES = [
    "good cheap seafood near Back Beach",
    "budget rice shop near city center",
    "where can I eat breakfast?",
    "place for late night drinks and cafe",
    "expensive fine dining with ocean view"
]

async def send_request(client, query):
    payload = {"query": query}
    try:
        response = await client.post(API_URL, json=payload, timeout=30.0)
        return response.json()
    except Exception as e:
        return {"success": False, "error_message": str(e), "total_latency_ms": 0}

async def run_load_test(num_requests, concurrent=1):
    print(f"Starting load test: {num_requests} requests, concurrency {concurrent}...")
    
    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        tasks = []
        results = []
        
        # We send them in batches according to concurrency
        for i in range(0, num_requests, concurrent):
            batch_queries = [TEST_QUERIES[(i+j) % len(TEST_QUERIES)] for j in range(min(concurrent, num_requests - i))]
            batch_tasks = [send_request(client, q) for q in batch_queries]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            print(f"Completed {len(results)}/{num_requests} requests...")
            
        total_time = time.perf_counter() - start_time

    return results, total_time

def analyze_results(results, total_time):
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    total_latency = [r.get("total_latency_ms", 0) for r in successful]
    retriever_latency = []
    reasoner_latency = []
    tokens_generated = []
    
    for r in successful:
        data = r.get("data", {})
        if "breakdown" in data:
            retriever_latency.append(data["breakdown"].get("retriever_ms", 0))
            reasoner_latency.append(data["breakdown"].get("reasoner_ms", 0))
            if "answer" in data:
                tokens = len(data["answer"].split()) * 1.3
                tokens_generated.append(tokens)
            
    print("\n" + "="*50)
    print("BENCHMARK RESULTS")
    print("="*50)
    print(f"Total requests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total time elapsed: {total_time:.2f} seconds")
    
    if total_time > 0:
        print(f"Throughput: {len(successful)/total_time:.2f} req/s")
        
    if successful:
        print("\n--- End-to-End Latency ---")
        print(f"Mean: {np.mean(total_latency):.2f} ms")
        print(f"p50:  {np.percentile(total_latency, 50):.2f} ms")
        print(f"p95:  {np.percentile(total_latency, 95):.2f} ms")
        print(f"Max:  {np.max(total_latency):.2f} ms")
        
        if retriever_latency:
            print("\n--- Retriever Latency ---")
            print(f"Mean: {np.mean(retriever_latency):.2f} ms")
            print(f"p50:  {np.percentile(retriever_latency, 50):.2f} ms")
            print(f"p95:  {np.percentile(retriever_latency, 95):.2f} ms")
            
        if reasoner_latency:
            print("\n--- Reasoner Latency ---")
            print(f"Mean: {np.mean(reasoner_latency):.2f} ms")
            print(f"p50:  {np.percentile(reasoner_latency, 50):.2f} ms")
            print(f"p95:  {np.percentile(reasoner_latency, 95):.2f} ms")
            if sum(reasoner_latency) > 0:
                # Convert reasoner latency sum to seconds for tps calculation
                reasoner_time_sec = sum(reasoner_latency) / 1000.0
                print(f"Tokens/sec: {sum(tokens_generated)/reasoner_time_sec:.2f} t/s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Food Buddy Load Test")
    parser.add_argument("-n", "--num", type=int, default=20, help="Total number of requests")
    parser.add_argument("-c", "--concurrent", type=int, default=1, help="Concurrent requests")
    args = parser.parse_args()
    
    results, total_time = asyncio.run(run_load_test(args.num, args.concurrent))
    analyze_results(results, total_time)
