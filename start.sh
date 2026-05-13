#!/bin/bash
set -e

echo "========================================"
echo " Convert-YT — Startup"
echo "========================================"

echo "[1/3] Updating yt-dlp..."
pip install --upgrade yt-dlp --quiet

YTDLP_VERSION=$(python -c "import yt_dlp; print(yt_dlp.version.__version__)" 2>/dev/null || echo "unknown")
echo "      yt-dlp version: $YTDLP_VERSION"

echo "[2/3] Preparing temp directory..."
mkdir -p "${TMP_DIR_PATH:-/tmp/Convert-YT}"

echo "[3/3] Starting server on port ${PORT:-8000}..."
echo "========================================"

exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 2 \
  --log-level info
