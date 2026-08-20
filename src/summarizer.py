import os
import time
from google import genai

PROMPT = """You are a daily AI briefing curator. Below are today's latest articles about AI and Agentic AI.

Create a concise, engaging briefing (max 400 words) with these sections:
🤖 **Agentic AI** — news about AI agents, autonomy, tool use
📰 **Industry & Research** — major AI developments, papers, product launches
⚡ **Quick Hits** — 1-liners for smaller items

Use bullet points. Keep it factual. Include the most important developments first.

Articles:
{articles}"""

# gemini-2.0-flash / gemini-2.0-flash-lite were retired on June 1, 2026.
# Current GA models, in preference order. Override with the GEMINI_MODELS
# env var (comma-separated) so model changes don't require a code edit.
DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]


def _models():
    override = os.environ.get("GEMINI_MODELS", "").strip()
    if override:
        return [m.strip() for m in override.split(",") if m.strip()]
    return list(DEFAULT_MODELS)


def format_raw_feed(articles):
    """Fallback briefing: a plain listing of scraped articles (no LLM needed)."""
    lines = ["🤖 **AI Briefing — Raw Feed**", ""]
    for a in articles[:6]:
        lines.append(f"• {a['title']}")
        lines.append(f"  {a['source']} — {a['url']}")
        lines.append("")
    if len(articles) > 6:
        lines.append(f"*+ {len(articles) - 6} more articles*")
    return "\n".join(lines)


def summarize(articles):
    if not articles:
        return "No news articles available today."
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("  ⚠️ No Gemini API key found — using raw feed fallback")
        return format_raw_feed(articles)

    client = genai.Client(api_key=api_key)
    articles_text = "\n".join(
        f"- {a['title']} ({a['source']})\n  {a['url']}"
        for a in articles
    )

    last_error = None
    for model in _models():
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=PROMPT.format(articles=articles_text),
                )
                return response.text
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = min(2 ** attempt * 5, 60)
                    print(f"  ⏳ Rate limited on {model}, retrying in {wait}s (attempt {attempt + 1})")
                    time.sleep(wait)
                else:
                    print(f"  ⚠️ {model} failed: {e}")
                    break

    # All models exhausted — fall back to raw article listing
    print(f"  ⚠️ All Gemini models failed ({last_error}) — falling back to raw feed")
    return format_raw_feed(articles)
