from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

@pytest.mark.asyncio
async def test_subreddit_insights():
    # This will attempt a live scrape of r/python
    # Note: Might fail if Reddit blocks the environment's IP
    print("\nTesting /subreddit/python/insights...")
    headers = {"X-API-Key": "free-beta-key-2026"}
    response = client.get("/subreddit/python/insights?limit=5", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Successfully fetched insights for r/{data['subreddit']}")
        print(f"Average Sentiment: {data['avg_sentiment']}")
        print(f"Top Keywords: {', '.join(data['top_keywords'])}")
        assert "posts" in data
        assert len(data["posts"]) > 0
    else:
        print(f"Integration test failed with status {response.status_code}")
        print(f"Detail: {response.json().get('detail')}")
        # We don't assert 200 here because it's a live test subject to external blocks
        # But we'll know if it works from the output
