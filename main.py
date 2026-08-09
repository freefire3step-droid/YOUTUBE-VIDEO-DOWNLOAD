import os
import time
import shutil
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
import yt_dlp

# Credentials
API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAGaD942GVyKt7oYv_KoCYqvtxKCN_PXcuE"

# In-memory session prevents Telegram session locks on server restart
app = Client(
    "PremiumYTBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

DOWNLOAD_BASE = "downloads"
os.makedirs(DOWNLOAD_BASE, exist_ok=True)

# Helper: Progress Bar Generator
def make_progress_bar(current, total):
    percentage = (current * 100 / total) if total > 0 else 0
    completed = int(percentage / 10)
    bar = "▓" * completed + "░" * (10 - completed)
    return bar, percentage

# Helper: File Size Formatter
def human_bytes(size):
    if not size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

# Helper: Time Formatter
def human_time(seconds):
    if not seconds:
        return "0s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

# Safe Status Progress Tracker (Avoids Rate Limits)
class ProgressTracker:
    def __init__(self, message, action_text):
        self.message = message
        self.action_text = action_text
        self.last_update = time.time()

    async def update_progress(self, current, total, speed=0, eta=0):
        now = time.time()
        # Update UI every 3 seconds to avoid Telegram rate limits
        if (now - self.last_update < 3) and (current < total):
            return
        self.last_update = now

        bar, pct = make_progress_bar(current, total)
        text = (
            f"✨ **{self.action_text}**\n\n"
            f"[{bar}] `{pct:.1f}%`\n\n"
            f"📦 **Downloaded:** `{human_bytes(current)}` / `{human_bytes(total)}`\n"
        )
        if speed > 0:
            text += f"🚀 **Speed:** `{human_bytes(speed)}/s`\n"
        if eta > 0:
            text += f"⏳ **ETA:** `{human_time(eta)}`"

        try:
            await self.message.edit_text(text)
        except (MessageNotModified, FloodWait):
            pass

def ytdlp_progress_hook(d, loop, tracker):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0) or 0
        eta = d.get('eta', 0) or 0

        if total > 0:
            asyncio.run_coroutine_threadsafe(
                tracker.update_progress(downloaded, total, speed, eta),
                loop
            )

YT_REGEX = r'(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|[^\s]+)'

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "👋 **Assalamu Alaikum!**\n\n"
        "Ami Premium YouTube Downloader Bot.\n"
        "Jekono **YouTube Video ba Shorts** link pathan, ami Live Progress soho fast download kore dibo! 🚀"
    )

@app.on_message(filters.text & filters.regex(YT_REGEX))
async def handle_yt(client, message):
    url = message.text.strip()
    status_msg = await message.reply_text("🔎 **Extracting Video Details...**")
    
    # Unique directory for this specific message request
    user_folder = os.path.join(DOWNLOAD_BASE, f"task_{message.id}_{int(time.time())}")
    os.makedirs(user_folder, exist_ok=True)

    loop = asyncio.get_event_loop()
    tracker = ProgressTracker(status_msg, "Downloading Video from YouTube")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best/b',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(user_folder, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000000000, # 2 GB Telegram Limit
        'geo_bypass': True,
        'nocheckcertificate': True,
        'progress_hooks': [lambda d: ytdlp_progress_hook(d, loop, tracker)],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'tv']
            }
        }
    }

    try:
        # Step 1: Download from YouTube
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        info = await loop.run_in_executor(None, download)
        if not info:
            await status_msg.edit_text("❌ Video details pawa jayni.")
            return

        title = info.get('title', 'YouTube Video')
        duration = info.get('duration', 0)

        # Locate downloaded file
        files = [os.path.join(user_folder, f) for f in os.listdir(user_folder) if not f.endswith('.temp')]
        if not files:
            await status_msg.edit_text("❌ File save hote somossa hoyeche.")
            return

        file_path = files[0]

        # Step 2: Upload to Telegram with Live Upload Progress Bar
        upload_tracker = ProgressTracker(status_msg, "Uploading to Telegram")

        async def upload_progress(current, total):
            await upload_tracker.update_progress(current, total)

        await message.reply_video(
            video=file_path,
            caption=f"🎬 **{title}**\n⏱ **Duration:** `{human_time(duration)}`",
            duration=int(duration),
            supports_streaming=True,
            progress=upload_progress
        )

        await status_msg.delete()

    except Exception as e:
        print(f"Error Log: {e}")
        await status_msg.edit_text(f"❌ **Error:** {str(e)[:150]}")

    finally:
        # Step 3: Absolute Cleanup to keep server storage 100% empty
        if os.path.exists(user_folder):
            try:
                shutil.rmtree(user_folder)
            except Exception as clean_err:
                print(f"Cleanup error: {clean_err}")

if __name__ == "__main__":
    print("🚀 Premium Bot initialized and running...")
    app.run()
