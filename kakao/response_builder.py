"""
카카오 i 오픈빌더 v2 응답 JSON 생성.
"""

_MAX_TEXT_LEN = 950  # 카카오톡 simpleText 안전 길이


def build_simple_text_response(text: str) -> dict:
    """단순 텍스트 응답."""
    if len(text) > _MAX_TEXT_LEN:
        text = text[: _MAX_TEXT_LEN - 3] + "..."
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ]
        },
    }


def build_list_card_response(title: str, items: list[dict], buttons: list[dict] | None = None) -> dict:
    """
    리스트 카드 응답.
    items: [{"title": str, "description": str}, ...]  (최대 5개)
    buttons: [{"label": str, "action": "message", "messageText": str}, ...]
    """
    card: dict = {
        "header": {"title": title},
        "items": items[:5],
    }
    if buttons:
        card["buttons"] = buttons[:2]

    return {
        "version": "2.0",
        "template": {
            "outputs": [{"listCard": card}]
        },
    }
