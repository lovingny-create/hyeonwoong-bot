"""
기능 2: 관측 방법 Q&A
Claude API를 통해 망원경 조작, CCD 촬영, 관측 기법 등 자유 질문 처리.
"""

from claude.client import ask_claude


async def handle(utterance: str) -> str:
    try:
        reply = await ask_claude(utterance)
    except Exception as e:
        return (
            "AI 응답 중 오류가 발생했습니다.\n\n"
            f"오류: {str(e)[:100]}\n\n"
            "잠시 후 다시 시도해 주세요."
        )
    # 카카오톡 안전 길이 제한
    if len(reply) > 950:
        reply = reply[:947] + "..."
    return reply
