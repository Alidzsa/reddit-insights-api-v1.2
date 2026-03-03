"""
RedSense v1.4 - Heavy Live Test Suite
Tests ALL endpoints on the live Hugging Face deployment.
"""

import asyncio
import httpx
import time
import json
import os

BASE_URL = "https://pedrothesixth-reddit-insights-api.hf.space"
API_KEY = "free-beta-key-2026"
HEADERS = {"X-API-Key": API_KEY}

# Support for Private Hugging Face Spaces
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    HEADERS["Authorization"] = f"Bearer {HF_TOKEN}"

SUBREDDITS = ["algeria", "python", "worldnews", "gaming"]
SEARCH_QUERIES = ["Algeria tech", "Darija", "AI news"]
USER_NAMES = ["spez", "kn0thing"]


async def test_endpoint(client, name, method, url, **kwargs):
    start = time.monotonic()
    try:
        resp = await client.request(method, url, headers=HEADERS, timeout=60.0, **kwargs)
        elapsed = time.monotonic() - start
        status = resp.status_code
        try:
            data = resp.json()
        except Exception:
            data = resp.text[:200]
        print(f"\n{'='*60}")
        print(f"[OK {status}] {name} ({elapsed:.2f}s)")
        if isinstance(data, list):
            print(f"   Items returned: {len(data)}")
            if data:
                print(f"   First item: {json.dumps(data[0], default=str)[:300]}")
        elif isinstance(data, dict):
            print(f"   Keys: {list(data.keys())}")
            print(f"   Preview: {json.dumps(data, default=str)[:300]}")
        return status == 200, elapsed, data
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"\n[FAIL] {name} ({elapsed:.2f}s): {e}")
        return False, elapsed, None


async def main():
    print("=" * 70)
    print("  REDSENSE v1.4 - HEAVY LIVE TEST SUITE")
    print(f"  Target: {BASE_URL}")
    print("=" * 70)

    post_ids = []
    results = []

    async with httpx.AsyncClient() as client:
        # 1. Health
        ok, lat, _ = await test_endpoint(client, "Health Check", "GET", f"{BASE_URL}/health")
        results.append(("Health", ok, lat))

        # 2. Root
        ok, lat, _ = await test_endpoint(client, "Root", "GET", f"{BASE_URL}/")
        results.append(("Root", ok, lat))

        # 3. Subreddit Insights
        for sub in SUBREDDITS:
            ok, lat, data = await test_endpoint(
                client, f"Insights: r/{sub}", "GET",
                f"{BASE_URL}/subreddit/{sub}/insights",
                params={"sort": "hot", "limit": 10}
            )
            results.append((f"Insights/{sub}", ok, lat))
            if ok and isinstance(data, dict) and data.get("posts"):
                pid = data["posts"][0].get("id")
                if pid and pid not in post_ids:
                    post_ids.append(pid)

        # 4. Hot Posts
        ok, lat, _ = await test_endpoint(
            client, "Hot Posts: r/algeria", "GET",
            f"{BASE_URL}/subreddit/algeria/hot", params={"limit": 10}
        )
        results.append(("Hot/algeria", ok, lat))

        # 5. Search
        for query in SEARCH_QUERIES:
            ok, lat, _ = await test_endpoint(
                client, f"Search: '{query}'", "GET",
                f"{BASE_URL}/search", params={"q": query, "limit": 10}
            )
            results.append((f"Search/'{query}'", ok, lat))

        # 6. Trending
        ok, lat, _ = await test_endpoint(
            client, "Trending (Algeria)", "GET",
            f"{BASE_URL}/trends/subreddits", params={"geo": "dz"}
        )
        results.append(("Trending/dz", ok, lat))

        # 7. Comment Intelligence (v1.4)
        if post_ids:
            for pid in post_ids[:2]:
                ok, lat, data = await test_endpoint(
                    client, f"Comments: /post/{pid[:6]}...", "GET",
                    f"{BASE_URL}/post/{pid}/comments", params={"limit": 20}
                )
                results.append((f"Comments/{pid[:6]}", ok, lat))
                if ok and isinstance(data, list) and data:
                    print(f"   Sentiment on first comment: {data[0].get('sentiment')}")
        else:
            print("\n[WARN] No post IDs found during subreddit scrape.")

        # 8. User Profile (v1.4)
        for user in USER_NAMES:
            ok, lat, _ = await test_endpoint(
                client, f"User Profile: {user}", "GET", f"{BASE_URL}/user/{user}"
            )
            results.append((f"User/{user}", ok, lat))

    # Summary
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    avg_lat = sum(lat for _, _, lat in results) / total
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print(f"  PASSED: {passed}/{total}   FAILED: {total-passed}/{total}   AVG LATENCY: {avg_lat:.2f}s")
    print("-" * 70)
    for name, ok, lat in results:
        tag = "[PASS]" if ok else "[FAIL]"
        print(f"  {tag} {name:<40} {lat:.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
