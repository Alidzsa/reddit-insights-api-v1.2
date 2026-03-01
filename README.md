---
title: Real-Time Reddit Community Insights API
emoji: 📊
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
---

# Real-Time Reddit Community Insights API (MVP v1.2)

A high-performance, 100% free-stack API designed to bypass Reddit's official API restrictions using advanced web scraping, stealth automation, and proxy rotation.

## 🚀 Vision
Built for developers and researchers who need real-time data from Reddit (subreddits, posts, trends) without the high costs or low rate limits of the official API. Optimized for regional growth segments like Algerian (`r/algeria`) and niche professional communities (`r/python`).

---

## 🛠️ Tech Stack (100% Free)
- **Framework**: FastAPI (Python) - High-speed REST endpoints.
- **Scraping Engine**: Playwright + `playwright-stealth` - Evades bot detection.
- **Data Source**: `old.reddit.com` - Lightweight HTML for faster parsing.
- **Insights**: VaderSentiment - Local NLP for instant sentiment scoring.
- **Proxy Management**: ProxyScrape (Free Tier API) - Integrated rotator with auto-validation.
- **Caching**: Redis (Self-hosted) with Local Memory Fallback - Minimizes redundant scraping.

---

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd APIprojectv2
   ```

2. **Set up Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

---

## ⚙️ Configuration
Create a `.env` file in the root directory (see `.env.example`):

```env
# Server Configuration
PORT=8000
DEBUG=True

# Proxy Configuration (Optional, falls back to local IP)
PROXY_SERVER=
PROXY_USERNAME=
PROXY_PASSWORD=

# Infrastructure
REDIS_URL=redis://localhost:6379
BROWSER_TIMEOUT=60000
```

---

## 🚦 Usage & Endpoints

### 1. Subreddit Insights
`GET /subreddit/{name}/insights?limit=10`
Returns real-time posts, average sentiment, and top keywords.
- **Example**: `GET /subreddit/python/insights`

### 2. Hot Post Trends
`GET /subreddit/{name}/hot?limit=25`
Returns hot posts with calculated trend velocity.

### 3. Regional Subreddit Trends (DZ Focus)
`GET /trends/subreddits?geo=dz`
Experimental endpoint for discovering trending subreddits in a specific geographic region.

### 4. Search Reddit
`GET /search?q=algérie&subreddit=algeria`
Search for keywords across Reddit or within a specific community.

### 5. Health & Diagnostics
`GET /health`
Returns real-time proxy pool status, scraping success rates, and system uptime.

---

## 📊 Example Response
```json
{
  "subreddit": "python",
  "avg_sentiment": 0.185,
  "top_keywords": ["fastapi", "scraping", "ai"],
  "posts": [...]
}
```

---

## 🛡️ Stealth & Anti-Bot Strategy
- **Hybrid Scraping**: Tries `.json` API first (1s latency) → Falls back to Playwright if blocked.
- **Proxy Rotation**: Automatic fetching from **200+ unique sources** (ProxyScrape, GitHub, etc.).
- **Fingerprinting**: Randomized User-Agents, Viewports, and Locales (`en-US`, `ar-DZ`, etc.).
- **Error Categorization**: Detects and logs Proxy Failures vs. Reddit Blocks for auto-recovery.

---

## 🧪 Testing
Run the heavy functionality test suite:
```powershell
.\venv\Scripts\python.exe tests/heavy_test.py
```

## 📜 Project Structure
- `app/core/`: Stealth browser, proxy manager, and cache logic.
- `app/services/`: Scraper service, proxy rotator, and insight engine.
- `app/models/`: Pydantic schemas for structured data.
- `tests/`: Integration and heavy functionality tests.

---

## ⚖️ License
MIT License. Free to use, adapt, and scale.
