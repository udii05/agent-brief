import os
from google import genai

PROMPT = """You are a daily AI briefing curator. Below are today's latest articles about AI and Agentic AI.

Create a concise, engaging briefing (max 400 words) with these sections:
🤖 **Agentic AI** — news about AI agents, autonomy, tool use
📰 **Industry & Research** — major AI developments, papers, product launches
⚡ **Quick Hits** — 1-liners for smaller items

Use bullet points. Keep it factual. Include the most important developments first.

Articles:
{articles}"""


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

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=PROMPT.format(articles=articles_text),
        )
        return response.text
    except Exception as e:
        return f"Error generating briefing: {e}"
