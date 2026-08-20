from src.summarizer import summarize, format_raw_feed


def test_summarize_no_articles():
    result = summarize([])
    assert "No news" in result


def test_summarize_no_key_falls_back_to_raw_feed(capfd):
    # No API key should still produce a usable briefing (raw feed), not an error.
    result = summarize([{"title": "Test", "url": "https://x.com", "source": "Test"}])
    assert "Raw Feed" in result
    assert "Test" in result
    assert "https://x.com" in result


def test_format_raw_feed():
    articles = [
        {"title": "One", "url": "https://a.com", "source": "Techcrunch"},
        {"title": "Two", "url": "https://b.com", "source": "Techcrunch"},
    ]
    result = format_raw_feed(articles)
    assert "Raw Feed" in result
    assert "• One" in result
    assert "Techcrunch — https://a.com" in result


def test_format_raw_feed_more_articles():
    articles = [{"title": f"Article {i}", "url": f"https://x.com/{i}",
                 "source": "Techcrunch"} for i in range(10)]
    result = format_raw_feed(articles)
    assert "*+ 4 more articles*" in result
