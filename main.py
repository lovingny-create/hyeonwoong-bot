"""
현웅봇 - 광주과학고등학교 천문 관측 도우미
카카오 i 오픈빌더 webhook 서버 (FastAPI)
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv()

from intent_router import classify_intent, dispatch
from kakao.request_parser import parse_utterance, parse_user_id
from kakao.response_builder import build_simple_text_response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="현웅봇", description="광주과학고 천문 관측 도우미")

_TIMEOUT_MSG = "처리 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."
_HELP_TEXT = """안녕하세요! 현웅봇입니다 🔭

광주과학고등학교 CDK14 망원경을 위한 천문 관측 도우미예요.

사용 예시:
• "오늘 밤 관측 대상 추천해줘"
• "시야각이 얼마야?"
• "UBVRI 필터 노출 시간 알려줘"
• "포커스 맞추는 방법이 뭐야?"
• "마운트 극축 맞추는 법 알려줘"

무엇이든 편하게 물어보세요!"""


@app.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    body = await request.json()
    utterance = parse_utterance(body)
    user_id = parse_user_id(body)

    logger.info(f"user={user_id[:8]}... utterance={utterance[:50]}")

    if not utterance:
        return JSONResponse(build_simple_text_response(_HELP_TEXT))

    # 도움말 요청
    if utterance in ("도움말", "help", "Help", "시작", "안녕", "안녕하세요"):
        return JSONResponse(build_simple_text_response(_HELP_TEXT))

    intent = classify_intent(utterance)
    logger.info(f"intent={intent.value}")

    try:
        text = await asyncio.wait_for(
            dispatch(intent, utterance),
            timeout=4.5,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout for utterance: {utterance[:50]}")
        text = _TIMEOUT_MSG
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        text = f"처리 중 오류가 발생했습니다.\n오류: {str(e)[:100]}"

    return JSONResponse(build_simple_text_response(text))


@app.get("/health")
async def health():
    return {"status": "ok", "bot": "현웅봇"}


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
