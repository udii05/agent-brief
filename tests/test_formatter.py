from src.formatter import format_briefing


def test_format_briefing_includes_date():
    result = format_briefing("Test summary")
    assert "AI Briefing" in result
    assert "Test summary" in result


def test_format_briefing_footer():
    result = format_briefing("Content")
    assert "Sent by Agent Brief" in result
    assert "8AM IST" in result
