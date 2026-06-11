from src.summarizer import summarize


def test_summarize_no_articles():
    result = summarize([])
    assert "No news" in result


def test_summarize_no_key(capfd):
    result = summarize([{"title": "Test", "url": "https://x.com", "source": "Test"}])
    assert result == "No Gemini API key found."
