# 현웅봇 🔭

광주과학고등학교 CDK14 천문 관측 도우미 카카오톡 챗봇

## 장비 사양

| 항목 | 모델 | 사양 |
|------|------|------|
| 망원경 | PlaneWave CDK14 | 356mm, f/7.2, fl=2563mm |
| 카메라 | Moravian C3-61000 PRO | Sony IMX455, 9576×6388, 3.76μm |
| 마운트 | MC700GE-2 | Hubo-i 컨트롤러, GPS |
| 필터 | UBVRI | 광대역 측광 필터 |

**계산값:** 플레이트 스케일 0.303″/px, 시야각 48.4'×32.3'

## 기능

1. **관측 대상 추천** - 현재 시각 기준 고도 30° 이상 관측 가능한 천체 추천
2. **관측 방법 Q&A** - 망원경 조작, CCD 촬영, 마운트 설정 등 Claude AI 답변
3. **시야각/노출 계산** - CDK14+C3-61000 PRO 기준 계산값 안내

## 설치 및 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 3. 서버 실행
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 카카오 i 오픈빌더 연결

1. [chatbot.kakao.com](https://chatbot.kakao.com) 접속
2. 봇 만들기 → "현웅봇" 생성
3. **스킬** 탭 → 스킬 추가 → 스킬 서버 URL: `https://서버주소/webhook`
4. **블록** 탭 → 폴백 블록 → 파라미터 설정 → 스킬 선택
5. 배포 → 카카오톡 채널 연결

### 로컬 개발 시 ngrok 사용

```bash
ngrok http 8000
# 출력된 https://xxxx.ngrok.io 를 스킬 서버 URL로 등록
```

## 동작 확인 (curl)

```bash
# 관측 대상 추천
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"userRequest": {"utterance": "오늘 밤 관측 대상 추천해줘", "user": {"id": "test"}}}'

# 시야각 계산
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"userRequest": {"utterance": "시야각 알려줘", "user": {"id": "test"}}}'

# Q&A
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"userRequest": {"utterance": "포커스 맞추는 방법 알려줘", "user": {"id": "test"}}}'
```

## 프로젝트 구조

```
hyeonwoong-bot/
├── main.py                 # FastAPI 앱, /webhook 엔드포인트
├── config.py               # 망원경 상수 (구경, 픽셀, 위치 등)
├── intent_router.py        # 키워드 기반 의도 분류
├── features/
│   ├── target_recommender.py  # 관측 대상 추천
│   ├── qa_handler.py          # Claude AI Q&A
│   └── fov_calculator.py      # 시야각/노출 계산
├── astronomy/
│   ├── catalog.py             # Messier + NGC 카탈로그
│   ├── visibility.py          # astroplan 가시성 계산
│   └── formatter.py           # 결과 → 한국어 텍스트
├── kakao/
│   ├── request_parser.py      # 카카오톡 요청 파싱
│   └── response_builder.py    # 카카오톡 v2 응답 생성
├── claude/
│   ├── system_prompt.py       # 시스템 프롬프트 (망원경 컨텍스트)
│   └── client.py              # Anthropic SDK 비동기 래퍼
├── .env.example
└── requirements.txt
```
