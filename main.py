import os
import glob
import asyncio
from pyrogram import Client, filters
import yt_dlp

API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAFWw7wkitpkWABUr_lAOq66aZ1KiSzT2H8"

app = Client("MasterYTBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YT_REGEX = r'(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/(watch\?v=|shorts/|[^\s]+)'

def download_yt(url, output_tmpl):
    ydl_opts = {
        # Auto-fallback format rules: Never fails regardless of video type
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best/b',
        'merge_output_format': 'mp4',
        'outtmpl': output_tmpl,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 2000000000, # 2 GB Limit
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'tv']
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        title = info.get('title', 'YouTube Video')
        return title, filename

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("👋 **Assalamu Alaikum!**\n\nYouTube Video ba Shorts link din, instant download hoye jabe.")

@app.on_message(filters.text & filters.regex(YT_REGEX))
async def yt_download_handler(client, message):
    url = message.text.strip()
    status_msg = await message.reply_text("⏳ **Video process kora hocche...** Ektu opekha korun.")

    output_tmpl = f"{DOWNLOAD_DIR}/{message.id}_%(id)s.%(ext)s"
    file_path = None

    try:
        loop = asyncio.get_event_loop()
        title, downloaded_file = await loop.run_in_executor(None, lambda: download_yt(url, output_tmpl))

        # Check if file exists or merged to mp4
        if os.path.exists(downloaded_file):
            file_path = downloaded_file
        else:
            files = glob.glob(f"{DOWNLOAD_DIR}/{message.id}_*")
            if files:
                file_path = files[0]

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ Download korte somossa hoyeche.")
            return

        await status_msg.edit_text("✅ **Download Complete!** Telegram e upload kora hocche...")

        # Upload to Telegram Group/Chat
        await message.reply_video(
            video=file_path,
            caption=f"🎬 **{title}**\n\n✅ Downloaded via Master Bot",
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        print(f"Error Log: {e}")
        await status_msg.edit_text(f"❌ **Error:** {str(e)[:150]}")

    finally:
        # GUARANTEED CLEANUP: Auto-delete from Railway storage instantly after sending
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        for f in glob.glob(f"{DOWNLOAD_DIR}/{message.id}_*"):
            try:
                os.remove(f)
            except Exception:
                pass

print("🚀 Bot running flawlessly...")
app.run()
