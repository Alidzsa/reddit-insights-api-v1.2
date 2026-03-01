from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.services.arabic_sentiment import arabic_sentiment
from typing import List, Dict
import re
from app.models.schemas import RedditPost
from datetime import datetime
from collections import Counter
import re

class InsightService:
    """
    Service to enrich Reddit data with sentiment and trend analysis.
    """
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, text: str) -> float:
        if not text:
            return 0.0
        # Simple Arabic detection (check for Arabic script)
        if re.search(r'[\u0600-\u06FF]', text):
            return arabic_sentiment.analyze(text)
            
        scores = self.analyzer.polarity_scores(text)
        return scores['compound']

    def calculate_trend_velocity(self, posts: List[RedditPost]) -> List[RedditPost]:
        # Simple velocity calculation based on score and time
        now = datetime.now().timestamp()
        for post in posts:
            age_hours = (now - post.created_utc) / 3600
            if age_hours > 0:
                post.trend_score = post.score / (age_hours + 2)**1.5
            else:
                post.trend_score = post.score
        return sorted(posts, key=lambda x: x.trend_score, reverse=True)

    def extract_keywords(self, posts: List[RedditPost], limit: int = 10) -> List[str]:
        all_text = " ".join([p.title for p in posts])
        words = re.findall(r'\w+', all_text.lower())
        
        # Filter out common stop-words (minimal list here)
        stop_words = {"the", "a", "an", "is", "are", "and", "or", "in", "to", "for", "of", "with", "this", "that"}
        filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]
        
        counter = Counter(filtered_words)
        return [word for word, count in counter.most_common(limit)]

insight_service = InsightService()
