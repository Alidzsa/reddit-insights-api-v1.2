import os
from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth import Stealth
from app.core.proxy_manager import proxy_manager
from app.services.proxy_rotator import proxy_rotator
import random

class StealthBrowser:
    """
    Wrapper around Playwright with stealth plugins and proxy support.
    """
    def __init__(self):
        self.headless = os.getenv("HEADLESS", "True").lower() == "true"
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))

    async def get_context(self, playwright) -> BrowserContext:
        # Try to get free proxy from rotator
        proxy_str = await proxy_rotator.get_proxy()
        proxy_config = None
        if proxy_str:
            proxy_config = {"server": f"http://{proxy_str}"}
        else:
            # Fallback to manual proxy if set
            proxy_config = proxy_manager.get_proxy_config()
        
        browser = await playwright.chromium.launch(
            headless=self.headless,
            proxy=proxy_config if proxy_config else None
        )
        
        # Free User-Agents List
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        
        context = await browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={"width": 1280, "height": 720},
            locale=random.choice(["en-US", "en-GB", "fr-DZ", "ar-DZ"])
        )
        
        # Apply stealth to the context
        # Note: stealth_async works on pages, so we'll apply it when creating a page
        return context

    async def create_stealth_page(self, context: BrowserContext):
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        return page

stealth_browser = StealthBrowser()
