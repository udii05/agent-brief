import os
from src.news_fetcher import fetch_news
from src.summarizer import summarize
from src.formatter import format_briefing


def main():
    print("Fetching news...")
    articles = fetch_news()
    print(f"Got {len(articles)} articles")

    print("Summarizing with Gemini...")
    summary = summarize(articles)

    print("Formatting briefing...")
    briefing = format_briefing(summary)

    with open("briefing.txt", "w", encoding="utf-8") as f:
        f.write(briefing)

    print("Briefing written to briefing.txt")


if __name__ == "__main__":
    main()
