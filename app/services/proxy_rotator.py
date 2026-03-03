import httpx
import random
import asyncio
import re
import time
from typing import List, Optional, Set
from datetime import datetime

class ProxyRotator:
    """
    Fetches, rotates, and VALIDATES free proxies from public sources. 
    Maintains a high-quality 'warm' pool to ensure low latency and high success.
    """
    def __init__(self):
        self.raw_proxies: Set[str] = set()
        self.validated_proxies: List[str] = []
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/archive/http.txt"
        ]
        self.is_checking = False
        self.last_refresh = 0

    async def refresh_proxies(self):
        """Fetch fresh candidate proxies from sources."""
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshing candidate proxy list...")
            async with httpx.AsyncClient() as client:
                for url in self.sources:
                    try:
                        response = await client.get(url, timeout=15.0)
                        if response.status_code == 200:
                            found = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{2,5}', response.text)
                            self.raw_proxies.update(found)
                    except: continue
            print(f"Total candidate proxies found: {len(self.raw_proxies)}")
            self.last_refresh = time.time()
        except Exception as e:
            print(f"Refresh failed: {e}")

    async def validate_proxy(self, proxy: str) -> bool:
        """Test if a proxy can reach Reddit with human-like latency."""
        try:
            async with httpx.AsyncClient(proxies=f"http://{proxy}", timeout=8.0) as client:
                # Use a specific Reddit asset that requires a real connection
                response = await client.get("https://www.reddit.com/static/pixel.png")
                return response.status_code == 200
        except:
            return False

    async def start_checker(self):
        """Background loop to maintain a pool of validated proxies."""
        if self.is_checking: return
        self.is_checking = True
        print("Starting Background Proxy Checker...")
        
        while True:
            try:
                # 1. Refresh raw list if empty or old (1 hour)
                if not self.raw_proxies or (time.time() - self.last_refresh > 3600):
                    await self.refresh_proxies()

                # 2. Pick a batch from raw to validate if our good pool is small
                if len(self.validated_proxies) < 50:
                    candidates = list(self.raw_proxies)[:100]
                    tasks = [self.validate_proxy(p) for p in candidates]
                    results = await asyncio.gather(*tasks)
                    
                    for proxy, is_valid in zip(candidates, results):
                        if is_valid:
                            if proxy not in self.validated_proxies:
                                self.validated_proxies.append(proxy)
                                if len(self.validated_proxies) >= 300: break
                        # Clean raw list to avoid re-checking same candidates quickly
                        if proxy in self.raw_proxies:
                            self.raw_proxies.remove(proxy)
                    
                    print(f"Validated pool size: {len(self.validated_proxies)}")

                # 3. Periodically re-validate a few from the 'good' pool to prune dead ones
                if self.validated_proxies:
                    num_to_test = min(10, len(self.validated_proxies))
                    test_sample = random.sample(self.validated_proxies, num_to_test)
                    for p in test_sample:
                        if not await self.validate_proxy(p):
                            self.validated_proxies.remove(p)
                            print(f"Pruned dead proxy from pool: {p}")

            except Exception as e:
                print(f"Error in proxy checker loop: {e}")

            await asyncio.sleep(60) # Run check every minute

    async def get_proxy(self) -> Optional[str]:
        """Returns a pre-validated proxy from the pool or None for local."""
        if not self.validated_proxies:
            # Emergency: try to validate some from raw if pool is empty
            if self.raw_proxies:
                candidates = list(self.raw_proxies)[:5]
                for p in candidates:
                    if await self.validate_proxy(p):
                        self.validated_proxies.append(p)
                        return p
            return None
        
        return random.choice(self.validated_proxies)

proxy_rotator = ProxyRotator()
