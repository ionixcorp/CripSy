def get_news_signal(news):
    if news is None:
        return "neutral", 0.0
    try:
        impact = news.get("impact", 0)
        direction = news.get("direction", "neutral")
        if impact > 0.7:
            return direction, impact
        else:
            return "neutral", 0.0
    except Exception:
        return "neutral", 0.0