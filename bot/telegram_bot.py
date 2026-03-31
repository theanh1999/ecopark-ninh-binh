#!/usr/bin/env python3
"""
Telegram Bot - Chỉnh sửa website Ecopark Ninh Bình qua Telegram
Sử dụng Gemini AI để hiểu lệnh và chỉnh sửa code tự động
"""

import os
import sys
import json
import re
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Telegram
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Gemini AI
from google import genai
from google.genai import types

# ============ CẤU HÌNH ============
# Load .env file nếu có
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = 'theanh1999/ecopark-ninh-binh'

# Đường dẫn repo local
REPO_DIR = os.environ.get('REPO_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Kiểm tra token
if not TELEGRAM_TOKEN or not GEMINI_API_KEY or not GITHUB_TOKEN:
    print("❌ Thiếu token! Tạo file bot/.env với nội dung:")
    print("   TELEGRAM_TOKEN=your_telegram_token")
    print("   GEMINI_API_KEY=your_gemini_key")
    print("   GITHUB_TOKEN=your_github_token")
    sys.exit(1)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Gemini client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def read_website_files():
    """Đọc tất cả file website hiện tại"""
    files = {}
    for fname in ['index.html', 'css/styles.css', 'js/main.js']:
        fpath = os.path.join(REPO_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                files[fname] = f.read()
    return files


def apply_changes(changes: dict):
    """Áp dụng thay đổi vào file"""
    results = []
    for fname, content in changes.items():
        fpath = os.path.join(REPO_DIR, fname)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        results.append(f"✅ {fname}")
    return results


def git_push(commit_msg):
    """Commit và push lên GitHub"""
    try:
        os.chdir(REPO_DIR)
        subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)

        # Set remote URL with token
        remote_url = f'https://theanh1999:{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git'
        subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], check=True, capture_output=True)
        subprocess.run(['git', 'push'], check=True, capture_output=True)

        # Remove token from URL
        clean_url = f'https://github.com/{GITHUB_REPO}.git'
        subprocess.run(['git', 'remote', 'set-url', 'origin', clean_url], capture_output=True)

        return True, "Push thành công!"
    except subprocess.CalledProcessError as e:
        return False, f"Lỗi git: {e.stderr.decode() if e.stderr else str(e)}"


def ask_gemini(user_message, website_files):
    """Gọi Gemini AI để xử lý yêu cầu chỉnh sửa"""

    system_prompt = """Bạn là trợ lý chỉnh sửa website Ecopark Ninh Bình. Website gồm 3 file:
- index.html: HTML chính
- css/styles.css: CSS styles
- js/main.js: JavaScript

Khi nhận yêu cầu chỉnh sửa, bạn phải:
1. Phân tích yêu cầu
2. Xác định file nào cần sửa
3. Trả về JSON với format:

```json
{
    "summary": "Mô tả ngắn thay đổi",
    "changes": {
        "tên_file": "nội dung file đầy đủ sau khi sửa"
    }
}
```

QUY TẮC QUAN TRỌNG:
- CHỈ trả về file CẦN SỬA, không trả về file không thay đổi
- Trả về NỘI DUNG ĐẦY ĐỦ của file (không phải diff)
- Giữ nguyên encoding UTF-8 và tiếng Việt có dấu
- Nếu yêu cầu không liên quan đến chỉnh sửa website, trả về:
```json
{"summary": "Câu trả lời của bạn", "changes": {}}
```
- Nếu yêu cầu không rõ ràng, hỏi lại trong summary và changes = {}
"""

    # Chuẩn bị nội dung file
    files_content = ""
    for fname, content in website_files.items():
        files_content += f"\n=== {fname} ===\n{content}\n"

    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(parts=[
                    types.Part.from_text(text=f"{system_prompt}\n\n--- FILE HIỆN TẠI ---\n{files_content}\n\n--- YÊU CẦU ---\n{user_message}")
                ])
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=65536,
            )
        )

        text = response.text.strip()

        # Tìm JSON block trong response
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Thử parse trực tiếp
        if text.startswith('{'):
            return json.loads(text)

        # Không tìm thấy JSON
        return {"summary": text, "changes": {}}

    except json.JSONDecodeError as e:
        return {"summary": f"⚠️ Lỗi parse JSON từ AI: {str(e)}", "changes": {}}
    except Exception as e:
        return {"summary": f"❌ Lỗi Gemini: {str(e)}", "changes": {}}


# ============ TELEGRAM HANDLERS ============

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start"""
    await update.message.reply_text(
        "🏗 *Website Ecopark Ninh Bình Bot*\n\n"
        "Gửi tin nhắn để chỉnh sửa website. Ví dụ:\n"
        "• `Đổi số điện thoại thành 0912345678`\n"
        "• `Thêm section FAQ`\n"
        "• `Đổi màu nền header thành xanh đậm`\n"
        "• `Cập nhật giá biệt thự thành 15-25 tỷ`\n"
        "• `Thay ảnh banner`\n\n"
        "📋 *Lệnh:*\n"
        "/status — Xem trạng thái website\n"
        "/preview — Link preview website\n"
        "/undo — Hoàn tác thay đổi cuối\n"
        "/help — Trợ giúp",
        parse_mode='Markdown'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem trạng thái website"""
    try:
        os.chdir(REPO_DIR)
        log = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
        await update.message.reply_text(
            f"📊 *Trạng thái website*\n\n"
            f"🔗 https://ecoparkninhbinh.org\n"
            f"📦 github.com/{GITHUB_REPO}\n\n"
            f"📝 *5 commit gần nhất:*\n```\n{log.stdout}```",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")


async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Link preview"""
    await update.message.reply_text(
        "🔗 *Preview website:*\n\n"
        "• https://ecoparkninhbinh.org\n"
        "• https://ecopark-ninh-binh.nguyentheanh1999hy.workers.dev",
        parse_mode='Markdown'
    )


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hoàn tác commit cuối"""
    try:
        os.chdir(REPO_DIR)
        subprocess.run(['git', 'revert', 'HEAD', '--no-edit'], check=True, capture_output=True)
        success, msg = git_push("Revert: hoàn tác thay đổi cuối qua Telegram bot")
        if success:
            await update.message.reply_text("↩️ Đã hoàn tác thay đổi cuối và push lên website!")
        else:
            await update.message.reply_text(f"❌ Hoàn tác thất bại: {msg}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn chỉnh sửa website"""
    user_msg = update.message.text
    if not user_msg:
        return

    # Bỏ qua lệnh bot
    if user_msg.startswith('/'):
        return

    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name or "User"

    # Thông báo đang xử lý
    processing_msg = await update.message.reply_text("⏳ Đang xử lý yêu cầu...")

    try:
        # Đọc file website hiện tại
        website_files = read_website_files()

        # Gọi Gemini AI
        result = ask_gemini(user_msg, website_files)
        summary = result.get('summary', 'Không có mô tả')
        changes = result.get('changes', {})

        if not changes:
            # Không có thay đổi — chỉ trả lời
            await processing_msg.edit_text(f"💬 {summary}")
            return

        # Áp dụng thay đổi
        applied = apply_changes(changes)

        # Cũng copy sang folder Website BDS
        for fname, content in changes.items():
            dest = os.path.join('/sessions/awesome-brave-ride/mnt/Website BDS', fname)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(content)

        # Git push
        commit_msg = f"[Telegram Bot] {summary}\n\nRequested by: {user_name}\nMessage: {user_msg}"
        success, push_msg = git_push(commit_msg)

        if success:
            files_list = '\n'.join(applied)
            await processing_msg.edit_text(
                f"✅ *Đã cập nhật website!*\n\n"
                f"📝 {summary}\n\n"
                f"📁 File đã sửa:\n{files_list}\n\n"
                f"🚀 Đã push lên GitHub → Cloudflare sẽ deploy trong 1-2 phút\n"
                f"🔗 https://ecoparkninhbinh.org",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(
                f"⚠️ Đã sửa file nhưng push thất bại:\n{push_msg}\n\n"
                f"📝 {summary}"
            )

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await processing_msg.edit_text(f"❌ Lỗi: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý ảnh gửi kèm — thay ảnh trên website"""
    caption = update.message.caption or ""
    photo = update.message.photo[-1]  # Lấy ảnh chất lượng cao nhất

    processing_msg = await update.message.reply_text("⏳ Đang xử lý ảnh...")

    try:
        # Download ảnh
        file = await context.bot.get_file(photo.file_id)

        # Xác định tên file từ caption
        name_map = {
            'hero': 'hero-banner.jpg',
            'banner': 'hero-banner.jpg',
            'overview': 'overview.jpg',
            'tổng quan': 'overview.jpg',
            'biệt thự': 'biet-thu.jpg',
            'biet thu': 'biet-thu.jpg',
            'shophouse': 'shophouse.jpg',
            'chung cư': 'chung-cu.jpg',
            'chung cu': 'chung-cu.jpg',
            'gallery': None,  # cần số
        }

        target_name = None
        caption_lower = caption.lower()

        for key, fname in name_map.items():
            if key in caption_lower:
                target_name = fname
                break

        # Gallery images
        gallery_match = re.search(r'gallery[- ]?(\d+)', caption_lower)
        if gallery_match:
            target_name = f"gallery-{gallery_match.group(1)}.jpg"

        if not target_name:
            target_name = 'hero-banner.jpg'  # Mặc định là hero

        # Download và lưu
        img_path = os.path.join(REPO_DIR, 'images', target_name)
        await file.download_to_drive(img_path)

        # Cũng copy sang Website BDS
        dest = os.path.join('/sessions/awesome-brave-ride/mnt/Website BDS/images', target_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        import shutil
        shutil.copy2(img_path, dest)

        # Git push
        commit_msg = f"[Telegram Bot] Thay ảnh {target_name}"
        success, push_msg = git_push(commit_msg)

        if success:
            await processing_msg.edit_text(
                f"✅ Đã thay ảnh `{target_name}` và push lên website!\n"
                f"🚀 Cloudflare deploy trong 1-2 phút",
                parse_mode='Markdown'
            )
        else:
            await processing_msg.edit_text(f"⚠️ Đã lưu ảnh nhưng push thất bại: {push_msg}")

    except Exception as e:
        await processing_msg.edit_text(f"❌ Lỗi xử lý ảnh: {str(e)}")


def main():
    """Khởi chạy bot"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(CommandHandler('preview', cmd_preview))
    app.add_handler(CommandHandler('undo', cmd_undo))
    app.add_handler(CommandHandler('help', cmd_start))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("🤖 Bot started! Listening for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
