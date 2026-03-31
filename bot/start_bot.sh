#!/bin/bash
# Khởi chạy Telegram Bot cho website Ecopark Ninh Bình
# Chạy: chmod +x start_bot.sh && ./start_bot.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "🤖 Ecopark Website Bot"
echo "======================"
echo "📁 Repo: $REPO_DIR"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa cài. Cài tại: https://python.org"
    exit 1
fi

# Tạo virtual env nếu chưa có
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate venv
source "$SCRIPT_DIR/venv/bin/activate"

# Cài dependencies
echo "📦 Cài đặt thư viện..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Set env
export REPO_DIR="$REPO_DIR"

# Chạy bot
echo "🚀 Khởi chạy bot..."
echo "💡 Nhấn Ctrl+C để dừng"
echo ""
python3 "$SCRIPT_DIR/telegram_bot.py"
