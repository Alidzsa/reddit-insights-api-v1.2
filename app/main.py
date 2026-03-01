from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import re
from typing import List, Optional
from app.services.scraper_service import scraper_service
from app.services.insight_service import insight_service
from app.services.proxy_rotator import proxy_rotator
from app.models.schemas import SubredditInsights, RedditPost, SearchRequest, RedditComment, UserProfile
from app.core.security import get_api_key
from app.core.stats_manager import stats_manager
from datetime import datetime
import os
import traceback

# Initialize FastAPI app
app = FastAPI(title="Real-Time Reddit Community Insights API")

# Initialize stats and limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Production Hardening: CORS & Trusted Hosts
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allowed_hosts = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,0.0.0.0,*.hf.space").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Real-Time Reddit Community Insights API", "status": "active"}

@app.get("/health")
async def health_check():
    """
    Returns real-time diagnostics, proxy pool size, and scraping success rates.
    """
    summary = stats_manager.get_summary()
    return {
        "status": "online",
        "timestamp": datetime.now(),
        "proxy_pool_size": len(proxy_rotator.proxies),
        "diagnostics": summary
    }

@app.get("/subreddit/{name}/insights", response_model=SubredditInsights)
@limiter.limit("30/minute")
async def get_subreddit_insights(
    request: Request, 
    name: str, 
    sort: str = "new", 
    limit: int = 25,
    api_key: str = Depends(get_api_key)
):
    """
    Fetch real-time posts and generate insights for a specific subreddit.
    """
    try:
        posts = await scraper_service.scrape_subreddit(name, sort, limit)
        if not posts:
            raise HTTPException(status_code=404, detail="Subreddit not found or no posts available")
            
        # Enrich with sentiment
        for post in posts:
            post.sentiment = insight_service.analyze_sentiment(post.title)
            
        avg_sentiment = sum([p.sentiment for p in posts]) / len(posts)
        keywords = insight_service.extract_keywords(posts)
        
        return SubredditInsights(
            subreddit=name,
            posts=posts,
            avg_sentiment=round(avg_sentiment, 3),
            top_keywords=keywords,
            last_updated=datetime.now()
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=List[RedditPost])
@limiter.limit("20/minute")
async def search_reddit(
    request: Request,
    q: str = Query(..., min_length=1),
    subreddit: Optional[str] = None,
    limit: int = 25,
    api_key: str = Depends(get_api_key)
):
    """
    Search Reddit for posts matching a query.
    """
    try:
        results = await scraper_service.search_reddit(q, subreddit, limit=limit)
        if not results:
             # If no results, maybe return empty list or 404
             return []
             
        # Optional: Enrich search results with sentiment
        for post in results:
            post.sentiment = insight_service.analyze_sentiment(post.title)
            
        return results
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subreddit/{name}/hot", response_model=List[RedditPost])
@limiter.limit("30/minute")
async def get_hot_posts(
    request: Request, 
    name: str, 
    limit: int = 25,
    api_key: str = Depends(get_api_key)
):
    """
    Fetch hot posts with trend velocity scoring.
    """
    try:
        posts = await scraper_service.scrape_subreddit(name, "hot", limit)
        return insight_service.calculate_trend_velocity(posts)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/post/{post_id}/comments", response_model=List[RedditComment])
@limiter.limit("20/minute")
async def get_post_comments(
    request: Request,
    post_id: str,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """
    Fetch comments for a specific post with built-in sentiment analysis.
    """
    try:
        comments = await scraper_service.scrape_post_comments(post_id, limit)
        
        # Enrich comments with sentiment (Recursive)
        def enrich_sentiment(comment_list):
            for comment in comment_list:
                comment.sentiment = insight_service.analyze_sentiment(comment.body)
                if comment.replies:
                    enrich_sentiment(comment.replies)
        
        enrich_sentiment(comments)
        return comments
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{username}", response_model=UserProfile)
@limiter.limit("15/minute")
async def get_user_profile(
    request: Request,
    username: str,
    api_key: str = Depends(get_api_key)
):
    """
    Fetch Reddit user profile intelligence.
    """
    try:
        profile = await scraper_service.scrape_user_profile(username)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends/subreddits")
@limiter.limit("10/minute")
async def get_trending_subreddits(
    request: Request, 
    geo: str = "dz",
    api_key: str = Depends(get_api_key)
):
    """
    Experimental: Get trending subreddits for a specific region.
    Defaulting to Algerian focus if geo=dz.
    """
    if geo == "dz":
        return {
            "geo": "Algeria",
            "trending_subreddits": ["algeria", "algiers", "dz", "arab"]
        }
    return {"geo": "Global", "trending_subreddits": ["worldnews", "technology", "gaming"]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
