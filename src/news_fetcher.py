import feedparser
import requests
import os
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "http://export.arxiv.org/rss/cs.AI",
    "https://hnrss.org/frontpage",
]

NEWSAPI_URL = "https://newsapi.org/v2/everything"
AI_KEYWORDS = ["ai", "artificial intelligence", "agent", "llm", "gpt",
               "language model", "neural", "deep learning", "machine learning",
               "agentic", "autonomous"]

# Direct-scrape fallback sources, used only if RSS + NewsAPI return nothing.
SCRAPE_URLS = [
    "https://techcrunch.com/category/artificial-intelligence/",
    "https://techcrunch.com/category/ai/",
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AgentBrief/1.0)"}

# TechCrunch article URLs are date-slugged: /YYYY/MM/DD/slug/
_ARTICLE_URL_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/")


class _LinkParser(HTMLParser):
    """Collects (href, visible text) pairs from a page."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            self._href = attrs.get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join("".join(self._text).split())
            if text:
                self.links.append((self._href, text))
            self._href = None
            self._text = []


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


def fetch_scrape():
    """Lightweight direct-scrape fallback (stdlib only) for when feeds fail."""
    articles = []
    for page_url in SCRAPE_URLS:
        try:
            resp = requests.get(page_url, timeout=15, headers=_HEADERS)
            resp.raise_for_status()
            parser = _LinkParser()
            parser.feed(resp.text)
            for href, text in parser.links:
                if len(text) < 20:
                    continue
                url = urljoin(page_url, href)
                if not url.startswith("http"):
                    continue
                # Only keep real article links (date-slugged), skip nav/category links
                if not _ARTICLE_URL_RE.search(url):
                    continue
                if not any(kw in text.lower() for kw in AI_KEYWORDS):
                    continue
                articles.append({
                    "title": text,
                    "url": url,
                    "published": "",
                    "source": "TechCrunch",
                })
            if articles:
                break
        except Exception as e:
            print(f"Scrape error ({page_url}): {e}")
    return articles


def _dedupe(articles):
    seen = set()
    unique = []
    for a in articles:
        t = a["title"].lower().strip()
        if t not in seen and len(t) > 10:
            seen.add(t)
            unique.append(a)
    return unique


def fetch_news():
    articles = _dedupe(fetch_rss() + fetch_newsapi())
    if not articles:
        print("  ⚠️ RSS/NewsAPI returned nothing — trying direct scrape")
        articles = _dedupe(fetch_scrape())
    return articles[:25]
