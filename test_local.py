"""
현웅봇 로컬 테스트 스크립트
카카오톡 연결 없이 각 기능을 직접 테스트합니다.

사용법:
    python test_local.py             # 전체 테스트
    python test_local.py fov         # 시야각 계산만
    python test_local.py recommend   # 관측 추천만
    python test_local.py qa          # Q&A만 (ANTHROPIC_API_KEY 필요)
    python test_local.py webhook     # webhook 엔드포인트 직접 테스트
"""

import asyncio
import sys
import time
import os
import json


def _header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)


def _result(text: str):
    print(text)
    print(f"\n[길이: {len(text)}자]")


# ─────────────────────────────────────────────────
# 기능 1: FOV 계산 (API 없음, 즉시 실행 가능)
# ─────────────────────────────────────────────────
async def test_fov():
    _header("기능3: 시야각/노출 계산")
    from features.fov_calculator import handle
    t0 = time.time()
    result = await handle("시야각 알려줘")
    elapsed = time.time() - t0
    _result(result)
    print(f"[응답 시간: {elapsed:.3f}s]")


# ─────────────────────────────────────────────────
# 기능 2: 관측 대상 추천 (astropy/astroplan 필요)
# ─────────────────────────────────────────────────
async def test_recommend():
    _header("기능1: 관측 대상 추천")
    from features.target_recommender import handle
    t0 = time.time()
    result = await handle("오늘 밤 관측 대상 추천해줘")
    elapsed = time.time() - t0
    _result(result)
    print(f"[응답 시간: {elapsed:.3f}s]")


# ─────────────────────────────────────────────────
# 기능 3: Q&A (ANTHROPIC_API_KEY 필요)
# ─────────────────────────────────────────────────
async def test_qa():
    _header("기능2: Claude AI Q&A")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[SKIP] ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("  .env 파일에 ANTHROPIC_API_KEY=sk-... 를 추가하세요.")
        return
    from features.qa_handler import handle
    question = "CDK14 망원경으로 포커스 맞추는 방법이 뭐야?"
    print(f"질문: {question}")
    t0 = time.time()
    result = await handle(question)
    elapsed = time.time() - t0
    _result(result)
    print(f"[응답 시간: {elapsed:.3f}s]")


# ─────────────────────────────────────────────────
# 의도 분류 테스트
# ─────────────────────────────────────────────────
def test_intent():
    _header("의도 분류 테스트")
    from intent_router import classify_intent, Intent

    cases = [
        ("오늘 밤 관측 대상 추천해줘",     Intent.TARGET_RECOMMEND),
        ("뭐 볼 수 있어?",               Intent.TARGET_RECOMMEND),
        ("시야각이 얼마야?",              Intent.FOV_CALC),
        ("UBVRI 필터 노출 시간 알려줘",    Intent.FOV_CALC),
        ("포커스 맞추는 법 알려줘",        Intent.QA),
        ("마운트 극축 어떻게 맞춰?",       Intent.QA),
    ]

    all_pass = True
    for utterance, expected in cases:
        got = classify_intent(utterance)
        status = "✓" if got == expected else "✗"
        if got != expected:
            all_pass = False
        print(f"  {status} \"{utterance}\"")
        if got != expected:
            print(f"      예상: {expected.value}, 실제: {got.value}")

    print(f"\n결과: {'전체 통과' if all_pass else '일부 실패'}")


# ─────────────────────────────────────────────────
# 카탈로그 통계
# ─────────────────────────────────────────────────
def test_catalog():
    _header("카탈로그 통계")
    from astronomy.catalog import FIXED_CATALOG, SOLAR_SYSTEM_TARGETS
    from config import LIMITING_MAG

    categories: dict = {}
    bright = 0
    for obj in FIXED_CATALOG:
        cat = obj.get("category", "미분류")
        categories[cat] = categories.get(cat, 0) + 1
        if obj["mag"] <= LIMITING_MAG:
            bright += 1

    print(f"고정 천체 총 수: {len(FIXED_CATALOG)}개")
    for cat, cnt in sorted(categories.items()):
        print(f"  {cat}: {cnt}개")
    print(f"한계등급({LIMITING_MAG}) 이내: {bright}개")
    print(f"태양계 천체: {len(SOLAR_SYSTEM_TARGETS)}개")


# ─────────────────────────────────────────────────
# 카카오톡 webhook 형식 시뮬레이션
# ─────────────────────────────────────────────────
async def test_webhook():
    _header("webhook JSON 형식 테스트 (카카오톡 시뮬레이션)")

    # 실제 카카오 i 오픈빌더가 보내는 형식
    payloads = [
        {
            "desc": "관측 추천",
            "body": {
                "userRequest": {
                    "utterance": "오늘 밤 뭐 볼 수 있어?",
                    "user": {"id": "test_user_001", "type": "botUserKey"},
                    "lang": "kr",
                    "timezone": "Asia/Seoul",
                }
            }
        },
        {
            "desc": "시야각 계산",
            "body": {
                "userRequest": {
                    "utterance": "시야각 알려줘",
                    "user": {"id": "test_user_001", "type": "botUserKey"},
                }
            }
        },
    ]

    from kakao.request_parser import parse_utterance
    from kakao.response_builder import build_simple_text_response
    from intent_router import classify_intent, dispatch

    for case in payloads:
        print(f"\n--- {case['desc']} ---")
        utterance = parse_utterance(case["body"])
        intent = classify_intent(utterance)
        print(f"발화: {utterance}")
        print(f"의도: {intent.value}")

        t0 = time.time()
        try:
            text = await asyncio.wait_for(dispatch(intent, utterance), timeout=4.5)
        except asyncio.TimeoutError:
            text = "처리 시간 초과"
        elapsed = time.time() - t0

        response = build_simple_text_response(text)
        response_json = json.dumps(response, ensure_ascii=False, indent=2)
        print(f"응답 JSON ({elapsed:.2f}s):")
        # 텍스트만 미리보기
        print(f"  text: {text[:100]}...")


# ─────────────────────────────────────────────────
# AAVSO 연결 테스트 (네트워크 필요)
# ─────────────────────────────────────────────────
async def test_aavso():
    _header("AAVSO VSX 연결 테스트")
    from astronomy.variable_stars import fetch_vsx_stars
    t0 = time.time()
    try:
        stars = await fetch_vsx_stars()
        elapsed = time.time() - t0
        source = "AAVSO" if stars and stars[0].get("source") == "aavso" else "Fallback"
        print(f"[{source}] {len(stars)}개 변광성 로드 ({elapsed:.2f}s)")
        if stars:
            s = stars[0]
            print(f"  샘플: {s['name']} | {s['type']} | {s.get('mag_range')}등급")
    except Exception as e:
        print(f"오류: {e}")


# ─────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────
async def main():
    # .env 로드
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    arg = sys.argv[1] if len(sys.argv) > 1 else "all"

    if arg == "fov":
        await test_fov()
    elif arg == "recommend":
        test_catalog()
        await test_recommend()
    elif arg == "qa":
        await test_qa()
    elif arg == "webhook":
        await test_webhook()
    elif arg == "aavso":
        await test_aavso()
    elif arg == "intent":
        test_intent()
    else:  # all
        test_intent()
        test_catalog()
        await test_fov()
        await test_aavso()
        await test_recommend()
        await test_qa()

    print("\n" + "="*50)
    print("  테스트 완료")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
