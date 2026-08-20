import argparse
import os
import sys

# Windows consoles default to cp1252 and can't print emoji in log lines.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.news_fetcher import fetch_news
from src.summarizer import summarize
from src.formatter import format_briefing


def main(send_whatsapp: bool = False):
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

    if send_whatsapp:
        from src.whatsapp_client import send_via_node
        send_via_node()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-whatsapp", action="store_true",
                        help="Send briefing via WhatsApp after generation")
    args = parser.parse_args()
    main(send_whatsapp=args.send_whatsapp)
