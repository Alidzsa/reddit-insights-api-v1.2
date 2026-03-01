import asyncio
import os
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from app.core.stealth_browser import stealth_browser
from app.core.cache_manager import cache_manager
from app.core.stats_manager import stats_manager
from app.models.schemas import RedditPost, RedditComment, UserProfile
from datetime import datetime
import random
import re
from typing import List, Optional
from app.services.proxy_rotator import proxy_rotator

class ScraperService:
    """
    Service to scrape Reddit data using old.reddit.com for light parsing.
    """
    def __init__(self):
        self.base_url = "https://old.reddit.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]

    async def _scrape_via_json(self, subreddit: Optional[str], sort: str, limit: int, query: Optional[str] = None) -> Optional[List[RedditPost]]:
        """Attempt to fetch data via Reddit's semi-public JSON endpoints."""
        if query:
            # Search query
            sub_part = f"r/{subreddit}/" if subreddit else ""
            url = f"{self.base_url}/{sub_part}search.json?q={query}&limit={limit}&sort={sort}&restrict_sr={'on' if subreddit else 'off'}"
        else:
            # Subreddit listing
            url = f"{self.base_url}/r/{subreddit}/{sort}.json?limit={limit}"

        try:
            async with httpx.AsyncClient(headers={"User-Agent": random.choice(self.user_agents)}) as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    posts = []
                    for child in children:
                        p_data = child.get("data", {})
                        posts.append(RedditPost(
                            id=p_data.get("id"),
                            title=p_data.get("title", "No Title"),
                            author=p_data.get("author", "unknown"),
                            score=p_data.get("score", 0),
                            num_comments=p_data.get("num_comments", 0),
                            created_utc=float(p_data.get("created_utc", 0)),
                            url=self.base_url + p_data.get("permalink", "") if p_data.get("permalink") else p_data.get("url", ""),
                            subreddit=p_data.get("subreddit", subreddit or "unknown")
                        ))
                    return posts
        except Exception as e:
            print(f"JSON fetch failed: {e}")
        return None

    async def scrape_subreddit(self, subreddit: str, sort: str = "new", limit: int = 25):
        cache_key = f"subreddit:{subreddit}:{sort}:{limit}"
        cached_data = cache_manager.get(cache_key)
        if cached_data:
            posts = [RedditPost(**p) if isinstance(p, dict) else p for p in cached_data]
            return posts

        # 1. Try JSON endpoint first (Much faster, less detection)
        json_posts = await self._scrape_via_json(subreddit, sort, limit)
        if json_posts:
            print(f"SUCCESS: Fetched r/{subreddit} via JSON API.")
            cache_manager.set(cache_key, [p.dict() for p in json_posts])
            stats_manager.record_event("json", True)
            return json_posts
        
        stats_manager.record_event("json", False)

        # 2. Fallback to Playwright browser if JSON fails
        print(f"JSON blocked. Falling back to Browser for r/{subreddit}...")
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with async_playwright() as p:
                    context = await stealth_browser.get_context(p)
                    page = await stealth_browser.create_stealth_page(context)
                    
                    # Random delay to mimic human behavior
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    url = f"{self.base_url}/r/{subreddit}/{sort}"
                    print(f"Attempt {attempt + 1}: Navigating to {url}")
                    
                    try:
                        response = await page.goto(url, wait_until="networkidle", timeout=60000)
                    except Exception as e:
                        stats_manager.record_event("browser", False, {"error_type": "proxy_errors", "detail": str(e)})
                        raise e

                    if not response:
                        raise Exception("No response from Reddit.")
                    
                    if response.status == 429:
                        stats_manager.record_event("browser", False, {"error_type": "reddit_blocks", "detail": "Rate limited (429)"})
                        raise Exception("Rate limited or blocked by Reddit.")

                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    posts = []
                    things = soup.select(".thing")
                    for thing in things[:limit]:
                        data = self._parse_post(thing, subreddit)
                        if data:
                            posts.append(data)
                            
                    await context.browser.close()
                    
                    if not posts:
                        stats_manager.record_event("browser", False, {"error_type": "reddit_blocks", "detail": "No posts found"})
                        raise Exception("No posts found (possibly blocked/empty page).")

                    # Cache the result for 5 minutes
                    cache_manager.set(cache_key, [p.dict() for p in posts])
                    stats_manager.record_event("browser", True)
                    return posts
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for r/{subreddit}: {str(e)}")
                last_error = e
                # Force proxy refresh for next attempt
                if "proxies" in dir(proxy_rotator):
                    proxy_rotator.proxies = [] 
                await asyncio.sleep(1)

        raise last_error

    async def search_reddit(self, query: str, subreddit: Optional[str] = None, sort: str = "relevance", limit: int = 25) -> List[RedditPost]:
        """Search Reddit for a query, optionally within a subreddit."""
        cache_key = f"search:{query}:{subreddit}:{sort}:{limit}"
        cached = cache_manager.get(cache_key)
        if cached:
            return [RedditPost(**p) for p in cached]

        # 1. Try JSON Search
        json_results = await self._scrape_via_json(subreddit, sort, limit, query)
        if json_results:
            cache_manager.set(cache_key, [p.dict() for p in json_results])
            stats_manager.record_event("json_search", True)
            return json_results

        stats_manager.record_event("json_search", False)
        
        # 2. Fallback to Browser Search
        print(f"JSON Search blocked. Falling back to Browser...")
        max_retries = 2
        for attempt in range(max_retries):
            try:
                async with async_playwright() as p:
                    context = await stealth_browser.get_context(p)
                    page = await stealth_browser.create_stealth_page(context)
                    
                    search_path = f"r/{subreddit}/" if subreddit else ""
                    url = f"{self.base_url}/{search_path}search?q={query}&sort={sort}&restrict_sr={'on' if subreddit else 'off'}"
                    
                    print(f"Search Attempt {attempt + 1}: Navigating to {url}")
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'lxml')
                    
                    posts = []
                    things = soup.select(".thing")
                    for thing in things[:limit]:
                        data = self._parse_post(thing, subreddit or "search_result")
                        if data:
                            posts.append(data)
                            
                    await context.browser.close()
                    if posts:
                        cache_manager.set(cache_key, [p.dict() for p in posts])
                        stats_manager.record_event("browser_search", True)
                        return posts
            except Exception as e:
                print(f"Browser Search Attempt {attempt + 1} failed: {e}")
                stats_manager.record_event("browser_search", False, {"error": str(e)})

        return []

    async def scrape_post_comments(self, post_id: str, limit: int = 50) -> List[RedditComment]:
        """Fetch comments for a specific post with sentiment support."""
        # Sanitize post_id (remove t3_ prefix if present)
        clean_id = post_id.replace("t3_", "")
        url = f"{self.base_url}/comments/{clean_id}.json?limit={limit}"
        
        try:
            async with httpx.AsyncClient(headers={"User-Agent": random.choice(self.user_agents)}) as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    # Reddit returns a list where the second element is the comment tree
                    comment_data = data[1].get("data", {}).get("children", [])
                    comments = []
                    for child in comment_data:
                        if child.get("kind") == "t1": # t1 is comment
                            comments.append(self._parse_comment(child.get("data", {})))
                    return comments
        except Exception as e:
            print(f"Comment fetch failed: {e}")
            
        return []

    async def scrape_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch basic user profile intelligence."""
        url = f"{self.base_url}/user/{username}/about.json"
        
        try:
            async with httpx.AsyncClient(headers={"User-Agent": random.choice(self.user_agents)}) as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    return UserProfile(
                        username=data.get("name", username),
                        karma=data.get("total_karma", 0),
                        created_utc=float(data.get("created_utc", 0)),
                        is_employee=data.get("is_employee", False),
                        is_gold=data.get("is_gold", False)
                    )
        except Exception as e:
            print(f"User profile fetch failed: {e}")
            
        return None

    def _parse_comment(self, data: dict, depth: int = 0) -> RedditComment:
        """Recursive parser for comment trees."""
        replies = []
        raw_replies = data.get("replies")
        if isinstance(raw_replies, dict):
            replies_data = raw_replies.get("data", {}).get("children", [])
            for r in replies_data:
                if r.get("kind") == "t1":
                    replies.append(self._parse_comment(r.get("data", {}), depth + 1))

        return RedditComment(
            id=data.get("id"),
            author=data.get("author", "unknown"),
            body=data.get("body", ""),
            score=data.get("score", 0),
            created_utc=float(data.get("created_utc", 0)),
            depth=depth,
            replies=replies
        )

    def _parse_post(self, thing, subreddit) -> RedditPost:
        try:
            post_id = thing.get("data-fullname", "")
            title_node = thing.select_one("a.title")
            title = title_node.text if title_node else "No Title"
            url = title_node.get("href", "") if title_node else ""
            if url.startswith("/"):
                url = self.base_url + url
                
            author = thing.get("data-author", "unknown")
            score = int(thing.get("data-score", 0))
            created_utc = float(thing.get("data-timestamp", 0)) / 1000
            num_comments = int(thing.get("data-comments-count", 0))
            
            return RedditPost(
                id=post_id,
                title=title,
                author=author,
                score=score,
                created_utc=created_utc,
                url=url,
                num_comments=num_comments,
                subreddit=subreddit
            )
        except Exception:
            return None

scraper_service = ScraperService()
