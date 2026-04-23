"""
Anthropic Claude API 클라이언트.
anthropic SDK는 동기 방식이므로 thread executor로 비동기 처리.
httpx Timeout으로 카카오톡 5초 제한 안에 응답 보장.
"""

import asyncio
import os

import anthropic
import httpx

from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS
from claude.system_prompt import SYSTEM_PROMPT

_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    timeout=httpx.Timeout(5.0, connect=2.0),
)


async def ask_claude(user_message: str, manual_context: str = "") -> str:
    """Claude API에 비동기로 질문하고 응답 텍스트 반환.

    Args:
        user_message: 사용자 질문
        manual_context: RAG로 검색된 매뉴얼 컨텍스트 (선택)
    """
    # 시스템 프롬프트에 매뉴얼 컨텍스트 추가
    system_with_context = SYSTEM_PROMPT
    if manual_context:
        system_with_context += f"\n\n{manual_context}"

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_with_context,
            messages=[{"role": "user", "content": user_message}],
        ),
    )
    return response.content[0].text
