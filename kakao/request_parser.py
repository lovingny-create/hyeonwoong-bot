"""
카카오 i 오픈빌더 webhook 요청 파싱.
"""


def parse_utterance(body: dict) -> str:
    """userRequest.utterance 에서 사용자 발화 추출."""
    return body.get("userRequest", {}).get("utterance", "").strip()


def parse_user_id(body: dict) -> str:
    """사용자 고유 ID 추출 (로깅용)."""
    return body.get("userRequest", {}).get("user", {}).get("id", "unknown")
