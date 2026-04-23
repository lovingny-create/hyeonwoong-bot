FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사 (manuals/ 제외 - .dockerignore 참고)
COPY . .

# entrypoint 스크립트 복사 및 실행 권한 부여
RUN chmod +x /app/entrypoint.sh

# 포트 노출
EXPOSE 8000

# 엔트리포인트: 시작 시 매뉴얼 다운로드 후 앱 실행
ENTRYPOINT ["/app/entrypoint.sh"]
