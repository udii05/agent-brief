from datetime import datetime


def format_briefing(summary_text: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    header = f"📬 *AI Briefing — {today}*\n\n"
    footer = "\n\n---\n🤖 Sent by Agent Brief · Daily at 8AM IST"
    return header + summary_text.strip() + footer
