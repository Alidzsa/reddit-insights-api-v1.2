from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class RedditPost(BaseModel):
    id: str
    title: str
    author: str
    score: int
    created_utc: float
    url: str
    num_comments: int
    selftext: Optional[str] = ""
    subreddit: str
    sentiment: Optional[float] = None
    trend_score: Optional[float] = None

class SubredditInsights(BaseModel):
    subreddit: str
    posts: List[RedditPost]
    avg_sentiment: float
    top_keywords: List[str]
    last_updated: datetime

class RedditComment(BaseModel):
    id: str
    author: str
    body: str
    score: int
    created_utc: float
    depth: int
    replies: List['RedditComment'] = []

class UserProfile(BaseModel):
    username: str
    karma: int
    created_utc: float
    recent_activity: List[Any]

class SearchRequest(BaseModel):
    query: str
    subreddit: Optional[str] = None
    timeframe: Optional[str] = "all"
    limit: Optional[int] = 25
