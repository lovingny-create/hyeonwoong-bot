"""
사용자 발화(utterance)에서 의도를 분류합니다.
카카오톡 5초 제한을 고려해 API 호출 없이 키워드 매칭으로 처리.
"""

from enum import Enum


class Intent(Enum):
    TARGET_RECOMMEND = "target"   # 관측 대상 추천
    FOV_CALC = "fov"              # 시야각/노출 계산
    QA = "qa"                     # 일반 Q&A (Claude API)


_RECOMMEND_KEYWORDS = [
    "추천", "관측 대상", "관측대상", "뭐 볼", "뭐볼", "어떤 천체",
    "오늘 밤", "오늘밤", "볼 수 있", "관측 가능", "관측가능",
    "오늘", "이번 주", "이번주",
]

_FOV_KEYWORDS = [
    "시야각", "화각", "fov", "FOV", "시야",
    "노출", "노출시간", "exposure",
    "플레이트 스케일", "plate scale",
    "화소", "픽셀",
    "UBVRI", "ubvri", "필터 노출",
]


def classify_intent(utterance: str) -> Intent:
    lower = utterance.lower()
    for kw in _RECOMMEND_KEYWORDS:
        if kw.lower() in lower:
            return Intent.TARGET_RECOMMEND
    for kw in _FOV_KEYWORDS:
        if kw.lower() in lower:
            return Intent.FOV_CALC
    return Intent.QA


async def dispatch(intent: Intent, utterance: str) -> str:
    from features.qa_handler import handle as qa_handle
    return await qa_handle(utterance)
