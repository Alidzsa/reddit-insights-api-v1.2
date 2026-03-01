import pytest
import asyncio
from app.services.insight_service import insight_service
from app.models.schemas import RedditPost

def test_sentiment_analysis():
    positive_text = "I love this new API, it works perfectly!"
    negative_text = "This is the worst service ever, I hate it."
    
    pos_score = insight_service.analyze_sentiment(positive_text)
    neg_score = insight_service.analyze_sentiment(negative_text)
    
    assert pos_score > 0
    assert neg_score < 0

def test_keyword_extraction():
    posts = [
        RedditPost(id="1", title="Python is great", author="u1", score=10, created_utc=0, url="", num_comments=0, subreddit="s"),
        RedditPost(id="2", title="I love Python programming", author="u2", score=10, created_utc=0, url="", num_comments=0, subreddit="s"),
        RedditPost(id="3", title="Coding in Python", author="u3", score=10, created_utc=0, url="", num_comments=0, subreddit="s"),
    ]
    keywords = insight_service.extract_keywords(posts)
    assert "python" in keywords

@pytest.mark.asyncio
async def test_trending_mock():
    # Placeholder for async tests if needed
    pass
