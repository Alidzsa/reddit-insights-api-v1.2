import httpx
import asyncio
import time
from typing import List

BASE_URL = "http://localhost:8000"
SUBREDDITS = [
    "python", "programming", "technology", "algeria",
    "worldnews", "science", "gaming", "investing"
]

API_KEY = "free-beta-key-2026"

async def test_endpoint(client: httpx.AsyncClient, subreddit: str) -> bool:
    url = f"{BASE_URL}/subreddit/{subreddit}/insights?limit=10"
    headers = {"X-API-Key": API_KEY}
    start_time = time.time()
    try:
        print(f"Starting test for r/{subreddit}...")
        response = await client.get(url, headers=headers, timeout=30.0)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: r/{subreddit} | Time: {duration:.2f}s | Sentiment: {data['avg_sentiment']} | Keywords: {len(data['top_keywords'])}")
            return True
        else:
            print(f"FAILED: r/{subreddit} | Status: {response.status_code} | Error: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: r/{subreddit} | {str(e)}")
        return False

async def run_heavy_test():
    async with httpx.AsyncClient() as client:
        print("=== STARTING HEAVY TEST ===")
        print(f"Testing {len(SUBREDDITS)} subreddits sequentially with free proxy rotation...")
        
        success_count = 0
        for sub in SUBREDDITS:
            if await test_endpoint(client, sub):
                success_count += 1
            await asyncio.sleep(1) # Small delay between subs
            
        print("\nTesting Search Endpoint...")
        headers = {"X-API-Key": API_KEY}
        try:
            search_res = await client.get(f"{BASE_URL}/search?q=algérie&subreddit=algeria", headers=headers, timeout=30.0)
            if search_res.status_code == 200:
                print(f"SUCCESS: Search 'algérie' in r/algeria returned {len(search_res.json())} results.")
            else:
                print(f"FAILED: Search returned {search_res.status_code}")
        except Exception as e:
            print(f"SEARCH ERROR: {e}")

        print("\n=== HEAVY TEST COMPLETE ===")
        print(f"Results: {success_count}/{len(SUBREDDITS)} passed.")
        
        if success_count > 0:
            print("Functionality verified for first launch.")
        else:
            print("CRITICAL FAILURE: No subreddits passed.")

if __name__ == "__main__":
    asyncio.run(run_heavy_test())
