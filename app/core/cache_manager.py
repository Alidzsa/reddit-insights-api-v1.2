import redis
import os
import json
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    """
    Manages caching using self-hosted Redis with local memory fallback.
    """
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            self.enabled = True
            print("Connected to Redis for caching.")
        except Exception:
            self.redis = None
            self.local_cache = {}
            self.enabled = False
            print("Redis unavailable. Using local memory fallback (not persistent).")

    def get(self, key: str) -> Optional[Any]:
        if self.redis:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        return self.local_cache.get(key)

    def set(self, key: str, value: Any, expire_seconds: int = 300):
        if self.redis:
            self.redis.set(key, json.dumps(value), ex=expire_seconds)
        else:
            self.local_cache[key] = value

cache_manager = CacheManager()
