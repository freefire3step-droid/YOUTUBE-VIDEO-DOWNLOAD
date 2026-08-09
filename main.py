import os
import glob
import asyncio
from pyrogram import Client, filters
import yt_dlp

# Credentials
API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAFWw7wkitpkWABUr_lAOq66aZ1KiSzT2H8"

app = Client("MasterYTBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary downloads folder
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Regex pattern for YouTube URLs (Shorts, Watch, Mobile Links)
YT_REGEX = r'(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|[^\s]+)'

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "👋 **Assalamu Alaikum!**\n\n"
        "Ami Master YouTube Downloader Bot. Group ba Inbox-e jekono YouTube Video/Shorts link din, ami instant download kore dibo."
    )

@app.on_message(filters.text & filters.regex(YT_REGEX))
async def yt_download_handler(client, message):
    url = message.text.strip()
    status_msg = await message.reply_text("⏳ **Video process kora hocche...** Ektu opekha korun.")

    file_path = None

    # YT-DLP Settings (Bypassing YouTube IP block & auto quality selection)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000000000, # 2 GB Telegram Limit
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    try:
        # Step 1: Download Video to Railway Local Storage
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: download_yt(url, ydl_opts))

        if not info:
            await status_msg.edit_text("❌ Video info pawa jayni.")
            return

        video_title = info.get('title', 'YouTube Video')
        video_id = info.get('id')

        # Find exact downloaded file
        downloaded_files = glob.glob(f"{DOWNLOAD_DIR}/{video_id}.*")
        if not downloaded_files:
            await status_msg.edit_text("❌ File save korte somossa hoyeche.")
            return

        file_path = downloaded_files[0]

        await status_msg.edit_text("✅ **Download Complete!** Ebar Telegram e upload kora hocche...")

        # Step 2: Upload Video to Telegram (Group/Chat)
        await message.reply_video(
            video=file_path,
            caption=f"🎬 **{video_title}**\n\n✅ Downloaded via Master Bot",
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        error_msg = str(e)
        print(f"Error Log: {error_msg}")
        await status_msg.edit_text(f"❌ **Error:** {error_msg[:150]}")

    finally:
        # Step 3: GUARANTEED STORAGE CLEANUP
        # Telegram e file chole jawar por Server storage static 0kb korar jonno file delete kora hocche
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned server file: {file_path}")
            except Exception as clean_err:
                print(f"Cleanup Error: {clean_err}")

        # Extra safety: Clean any leftovers in downloads folder
        for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
            try:
                os.remove(f)
            except Exception:
                pass

def download_yt(url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)

print("🚀 Master YT Downloader Bot is Running smoothly...")
app.run()
