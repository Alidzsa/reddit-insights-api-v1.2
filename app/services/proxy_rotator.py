import httpx
import random
import asyncio
import re
from typing import List, Optional

class ProxyRotator:
    """
    Fetches and rotates free proxies from ProxyScrape and other public sources.
    """
    def __init__(self):
        self.proxies: List[str] = []
        # Free sources (ProxyScrape + GitHub curated lists)
        self.sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/archive/http.txt"
        ]
        self.last_refresh = 0

    async def refresh_proxies(self):
        """Fetch fresh list of free proxies from multiple sources."""
        try:
            new_proxies = set()
            async with httpx.AsyncClient() as client:
                for url in self.sources:
                    try:
                        response = await client.get(url, timeout=10.0)
                        if response.status_code == 200:
                            # Robust regex for IP:Port
                            found = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{2,5}', response.text)
                            new_proxies.update(found)
                    except:
                        continue
            
            p_list = list(new_proxies)
            random.shuffle(p_list)
            self.proxies = p_list[:300] # Increased pool to 300 for better rotation
            print(f"Refreshed proxy pool: {len(self.proxies)} valid unique proxies.")
        except Exception as e:
            print(f"Failed to refresh proxies: {e}")

    async def validate_proxy(self, proxy: str) -> bool:
        """Test if a proxy can reach Reddit."""
        try:
            async with httpx.AsyncClient(proxies=f"http://{proxy}", timeout=5.0) as client:
                response = await client.get("https://www.reddit.com/static/pixel.png")
                return response.status_code == 200
        except Exception:
            return False

    async def get_proxy(self) -> Optional[str]:
        """Get a validated random proxy from the pool or return None for local IP."""
        if not self.proxies:
            await self.refresh_proxies()
        
        # Try up to 5 random proxies from the list
        for _ in range(5):
            if not self.proxies:
                break
            proxy = random.choice(self.proxies)
            if await self.validate_proxy(proxy):
                print(f"Using validated proxy: {proxy}")
                return proxy
            else:
                self.proxies.remove(proxy)
        
        print("No working free proxies found. Falling back to local IP.")
        return None

proxy_rotator = ProxyRotator()
