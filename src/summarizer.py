import os
import time
from google import genai
from google.genai import types

PROMPT = """You are a daily AI briefing curator. Below are today's latest articles about AI and Agentic AI.

Create a concise, engaging briefing (max 400 words) with these sections:
🤖 **Agentic AI** — news about AI agents, autonomy, tool use
📰 **Industry & Research** — major AI developments, papers, product launches
⚡ **Quick Hits** — 1-liners for smaller items

Use bullet points. Keep it factual. Include the most important developments first.

Articles:
{articles}"""

MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]


def summarize(articles):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "No Gemini API key found."
    if not articles:
        return "No news articles available today."

    client = genai.Client(api_key=api_key)
    articles_text = "\n".join(
        f"- {a['title']} ({a['source']})\n  {a['url']}"
        for a in articles
    )

    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=PROMPT.format(articles=articles_text),
                )
                return response.text
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = min(2 ** attempt * 5, 60)
                    print(f"  ⏳ Rate limited on {model}, retrying in {wait}s (attempt {attempt + 1})")
                    time.sleep(wait)
                else:
                    if model != MODELS[-1]:
                        print(f"  ⚠️ {model} failed, trying next model...")
                        break
                    return f"Error generating briefing: {e}"

    # All models exhausted — fall back to raw article listing
    print("  ⚠️ All models exhausted, falling back to raw article list")
    lines = ["🤖 **AI Briefing — Raw Feed**", ""]
    for a in articles[:6]:
        lines.append(f"• {a['title']}")
        lines.append(f"  {a['source']} — {a['url']}")
        lines.append("")
    if len(articles) > 6:
        lines.append(f"*+ {len(articles) - 6} more articles*")
    return "\n".join(lines)
