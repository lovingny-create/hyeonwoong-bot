#!/bin/bash
set -e

echo "[startup] Checking for manuals..."

# GitHub release에서 매뉴얼 다운로드 (로컬에 없으면)
if [ ! -d "manuals" ] || [ -z "$(ls -A manuals)" ]; then
    echo "[startup] Downloading manuals from GitHub Releases..."
    curl -L -o manuals.tar.gz https://github.com/lovingny-create/hyeonwoong-bot/releases/download/v1.0-manuals/manuals.tar.gz
    tar -xzf manuals.tar.gz
    rm manuals.tar.gz
    echo "[startup] ✓ Manuals downloaded and extracted"
else
    echo "[startup] ✓ Manuals folder already exists"
fi

echo "[startup] Starting application..."
exec python main.py
