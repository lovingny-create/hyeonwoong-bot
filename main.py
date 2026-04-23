"""
현웅봇 - 광주과학고등학교 천문 관측 도우미
카카오 i 오픈빌더 webhook 서버 (FastAPI)
"""

import asyncio
import json
import logging
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse

load_dotenv()

from intent_router import classify_intent, dispatch
from kakao.request_parser import parse_utterance, parse_user_id
from kakao.response_builder import build_simple_text_response
from claude.rag_loader import load_pdf_to_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 서버 시작 시 RAG 데이터베이스 로드
logger.info("Loading PDF manuals into RAG database...")
load_pdf_to_db()

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
    # 한글 인코딩 문제 해결: raw body를 UTF-8로 명시적 디코딩 (오류 무시)
    raw_body = await request.body()
    body = json.loads(raw_body.decode('utf-8', errors='replace'))
    utterance = parse_utterance(body)
    user_id = parse_user_id(body)

    logger.info(f"user={user_id[:8]}... utterance={utterance[:50]}")

    if not utterance:
        return JSONResponse(build_simple_text_response(_HELP_TEXT))

    # 도움말 요청
    if utterance in ("도움말", "help", "Help", "시작", "안녕", "안녕하세요", "안냥", "hi", "Hi", "hello"):
        return JSONResponse(build_simple_text_response(_HELP_TEXT))

    intent = classify_intent(utterance)
    logger.info(f"intent={intent.value}")

    try:
        result = await asyncio.wait_for(
            dispatch(intent, utterance),
            timeout=7.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout for utterance: {utterance[:50]}")
        result = _TIMEOUT_MSG
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        result = f"처리 중 오류가 발생했습니다.\n오류: {str(e)[:100]}"

    # dict → 이미 카카오 JSON 응답 (카루셀 등), str → simpleText로 감싸기
    if isinstance(result, dict):
        return JSONResponse(result)
    return JSONResponse(build_simple_text_response(result))


@app.get("/")
async def chat_page() -> HTMLResponse:
    html = pathlib.Path("templates/chat.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.post("/chat")
async def chat_api(request: Request) -> JSONResponse:
    body = await request.json()
    utterance = body.get("message", "").strip()

    if not utterance:
        return JSONResponse({"reply": "메시지를 입력해주세요."})

    logger.info(f"web_chat: utterance={utterance[:50]}")

    try:
        intent = classify_intent(utterance)
        result = await asyncio.wait_for(
            dispatch(intent, utterance),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Web chat timeout: {utterance[:50]}")
        result = "응답 시간이 초과되었습니다. 다시 시도해 주세요."
    except Exception as e:
        logger.error(f"Web chat error: {e}", exc_info=True)
        result = f"오류가 발생했습니다: {str(e)[:100]}"

    if isinstance(result, dict):
        result = str(result)
    return JSONResponse({"reply": result})


@app.get("/health")
async def health():
    return {"status": "ok", "bot": "현웅봇"}


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    # Production 환경에서는 reload 비활성화 (파일 감시로 인한 자동 재시작 방지)
    reload = os.environ.get("ENVIRONMENT") != "production"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
