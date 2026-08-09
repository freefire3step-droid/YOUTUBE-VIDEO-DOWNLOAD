import os
from pyrogram import Client, filters
import yt_dlp
import time

# Apnar Credentials
API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAFWw7wkitpkWABUr_lAOq66aZ1KiSzT2H8"

# Pyrogram Client Setup
app = Client("MyYtBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command Handler
@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        f"Hello {message.from_user.first_name}! 👋\n"
        "Ami ekta YouTube downloader bot. Jekono YouTube video'r link ekhane send korun, ami download kore dibo."
    )

# YouTube Link Handler
@app.on_message(filters.text & filters.regex(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+'))
async def download_video(client, message):
    url = message.text
    status_msg = await message.reply_text("⏳ **Video process kora hocche, ektu opekha korun...** (Long video hole kichukhon somoy lagte pare)")

    # yt-dlp Settings (Boro file manage korar jonno)
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # Best quality MP4 format
        'outtmpl': '%(id)s.%(ext)s',     # File er nam save hobe video ID diye
        'quiet': True,
        'max_filesize': 2000000000       # Telegram limit (2 GB max)
    }

    try:
        # Video Download korche Railway server e
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            video_title = info.get('title', 'YouTube Video')

        await status_msg.edit_text("✅ **Download Complete!** Ebar Telegram e upload kora hocche...")

        # Server theke Telegram e user ke pathacche
        await message.reply_video(
            video=file_path,
            caption=f"🎬 **{video_title}**\n\n✅ Downloaded via Bot",
            supports_streaming=True # Ete user video download korar agei play kore dekhte parbe
        )
        
        # Upload complete howar por status message delete korche
        await status_msg.delete()

        # Railway server theke file delete korche space bachanor jonno
        if os.path.exists(file_path):
            os.remove(file_path)

    except yt_dlp.utils.DownloadError:
        await status_msg.edit_text("❌ **Error:** Video ti download kora jacche na. File size ki 2GB er theke boro?")
    except Exception as e:
        await status_msg.edit_text(f"❌ **Oshubidha hoyeche:** {str(e)}")

print("Bot is running...")
app.run()
