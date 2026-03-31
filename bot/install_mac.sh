#!/bin/bash
# Cài đặt bot chạy tự động khi mở máy Mac
# Chạy: chmod +x install_mac.sh && ./install_mac.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="org.ecoparkninhbinh.bot"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$HOME/Library/Logs/EcoparkBot"

echo "🤖 Cài đặt Ecopark Bot tự động khởi chạy"
echo "==========================================="

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa cài. Cài tại: https://python.org"
    exit 1
fi

# Tạo virtual env
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

source "$SCRIPT_DIR/venv/bin/activate"
echo "📦 Cài đặt thư viện..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Kiểm tra file .env
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Chưa có file .env!"
    echo "   Chạy: cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    echo "   Rồi điền token vào file .env"
    exit 1
fi

# Đọc token từ .env
source "$ENV_FILE"
if [ -z "$TELEGRAM_TOKEN" ] || [ -z "$GEMINI_API_KEY" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Thiếu token trong .env! Cần: TELEGRAM_TOKEN, GEMINI_API_KEY, GITHUB_TOKEN"
    exit 1
fi

# Tạo log directory
mkdir -p "$LOG_DIR"

# Tạo LaunchAgent plist
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${SCRIPT_DIR}/venv/bin/python3</string>
        <string>${SCRIPT_DIR}/telegram_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>REPO_DIR</key>
        <string>${REPO_DIR}</string>
        <key>TELEGRAM_TOKEN</key>
        <string>${TELEGRAM_TOKEN}</string>
        <key>GEMINI_API_KEY</key>
        <string>${GEMINI_API_KEY}</string>
        <key>GITHUB_TOKEN</key>
        <string>${GITHUB_TOKEN}</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/bot.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/bot-error.log</string>
    <key>ThrottleInterval</key>
    <integer>30</integer>
</dict>
</plist>
PLIST

echo "✅ LaunchAgent tạo tại: $PLIST_PATH"

# Load LaunchAgent
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo ""
echo "✅ Bot đã được cài đặt và khởi chạy!"
echo ""
echo "📋 Các lệnh hữu ích:"
echo "  Xem log:    tail -f ~/Library/Logs/EcoparkBot/bot.log"
echo "  Dừng bot:   launchctl unload $PLIST_PATH"
echo "  Chạy lại:   launchctl load $PLIST_PATH"
echo "  Gỡ cài đặt: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
