from src.news_fetcher import fetch_news


def test_fetch_returns_list():
    articles = fetch_news()
    assert isinstance(articles, list)


def test_article_has_required_keys():
    from src.news_fetcher import fetch_news
    articles = fetch_news()
    if articles:
        for a in articles:
            assert "title" in a
            assert "url" in a
            assert "source" in a
