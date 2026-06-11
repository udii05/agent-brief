import feedparser
import requests
import os
from datetime import datetime, timezone

RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "http://export.arxiv.org/rss/cs.AI",
    "https://hnrss.org/frontpage",
]

NEWSAPI_URL = "https://newsapi.org/v2/everything"
AI_KEYWORDS = ["ai", "artificial intelligence", "agent", "llm", "gpt",
               "language model", "neural", "deep learning", "machine learning",
               "agentic", "autonomous"]


def fetch_rss():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed_url.split("/")[2]
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                if "hnrss" in source:
                    if not any(kw in title.lower() for kw in AI_KEYWORDS):
                        continue
                articles.append({
                    "title": title,
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": source.split(".")[0].capitalize(),
                })
        except Exception as e:
            print(f"RSS error ({feed_url}): {e}")
    return articles


def fetch_newsapi():
    api_key = os.environ.get("NEWSAPI_KEY", "")
    if not api_key:
        return []
    try:
        params = {
            "q": "Agentic AI OR artificial intelligence",
            "apiKey": api_key,
            "language": "en",
            "pageSize": 15,
            "sortBy": "publishedAt",
        }
        resp = requests.get(NEWSAPI_URL, params=params, timeout=10)
        data = resp.json()
        articles = []
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published": item.get("publishedAt", ""),
                "source": item.get("source", {}).get("name", "NewsAPI"),
            })
        return articles
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []


def fetch_news():
    articles = fetch_rss() + fetch_newsapi()
    seen = set()
    unique = []
    for a in articles:
        t = a["title"].lower().strip()
        if t not in seen and len(t) > 10:
            seen.add(t)
            unique.append(a)
    return unique[:25]
