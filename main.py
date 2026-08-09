import os
import glob
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters
import yt_dlp

API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAFWw7wkitpkWABUr_lAOq66aZ1KiSzT2H8"

app = Client("MasterYTBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YT_REGEX = r'(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|[^\s]+)'

# Method 1: Cobalt API (No Cookies Required - Cloud Block Bypass)
async def download_via_cobalt(url, file_path):
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "videoQuality": "720" # Fast & High Quality
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    video_url = data.get("url")
                    if video_url:
                        async with session.get(video_url) as vid_resp:
                            if vid_resp.status == 200:
                                async with aiofiles.open(file_path, 'wb') as f:
                                    while True:
                                        chunk = await vid_resp.content.read(1024 * 1024)
                                        if not chunk:
                                            break
                                        await f.write(chunk)
                                return True
        return False
    except Exception as e:
        print(f"Cobalt Engine Bypass Failed: {e}")
        return False

# Method 2: yt-dlp with iOS/TV Client Spoofing (Fallback)
def download_via_ytdlp(url, output_tmpl):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_tmpl,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000000000,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'tv_embedded', 'mweb']
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get('title', 'YouTube Video')

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("👋 **Assalamu Alaikum!**\n\nVideo ba Shorts link din, instant download hoye jabe.")

@app.on_message(filters.text & filters.regex(YT_REGEX))
async def yt_download_handler(client, message):
    url = message.text.strip()
    status_msg = await message.reply_text("⏳ **Video process kora hocche...** Ektu opekha korun.")

    file_path = f"{DOWNLOAD_DIR}/{message.id}.mp4"
    video_title = "YouTube Video"
    success = False

    try:
        # Step 1: Try Cobalt Engine (No cookie bypass)
        success = await download_via_cobalt(url, file_path)

        # Step 2: If Cobalt fails, fallback to yt-dlp iOS Client Bypass
        if not success:
            loop = asyncio.get_event_loop()
            video_title = await loop.run_in_executor(None, lambda: download_via_ytdlp(url, f"{DOWNLOAD_DIR}/%(id)s.%(ext)s"))
            downloaded_files = glob.glob(f"{DOWNLOAD_DIR}/*")
            if downloaded_files:
                file_path = downloaded_files[0]
                success = True

        if not success or not os.path.exists(file_path):
            await status_msg.edit_text("❌ Video download kora jayni. Onno ekta link try korun.")
            return

        await status_msg.edit_text("✅ **Download Complete!** Uploading to Telegram...")

        # Upload to Group/Chat
        await message.reply_video(
            video=file_path,
            caption=f"🎬 **{video_title}**\n\n✅ Downloaded Successfully",
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)[:150]}")

    finally:
        # GUARANTEED CLEANUP: Auto-delete from Railway storage instantly
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
            try:
                os.remove(f)
            except Exception:
                pass

print("🚀 Master Bot is running with Auto Bypass...")
app.run()
