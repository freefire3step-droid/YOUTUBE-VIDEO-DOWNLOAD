import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

API_ID = 33019465
API_HASH = "02fe1be68e1f501bb36dcfc55e8014ca"
BOT_TOKEN = "8899267959:AAGaD942GVyKt7oYv_KoCYqvtxKCN_PXcuE"

app = Client(
    "yt_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ডাউনলোড ফোল্ডার তৈরি
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text("হ্যালো! গ্রুপে বা ইনবক্সে যেকোনো YouTube ভিডিওর লিঙ্ক দিন, আমি ডাউনলোড করে দিচ্ছি।")

# filters.private সরিয়ে দেওয়া হয়েছে, তাই এটি গ্রুপেও কাজ করবে
@app.on_message(filters.text)
async def download_yt(client: Client, message: Message):
    url = message.text.strip()

    # মেসেজে ইউটিউব লিংক না থাকলে বট চুপ থাকবে (গ্রুপের অন্যান্য মেসেজে কোনো রিপ্লাই দেবে না)
    if not ("youtube.com" in url or "youtu.be" in url):
        return

    # যে মেসেজে লিংক দেওয়া হয়েছে, ঠিক তাকে কোট (quote) করে রিপ্লাই দেবে
    msg = await message.reply_text("লিঙ্ক পেয়েছি! প্রসেস করা হচ্ছে...", quote=True)

    # Unique Filename (গ্রুপের একাধিক ইউজার একসাথে রিকোয়েস্ট করলেও ফাইল মিক্স হবে না)
    user_id = message.from_user.id if message.from_user else message.chat.id
    file_id_name = f"downloads/{user_id}_{message.id}"
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{file_id_name}.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    file_path = None
    try:
        await msg.edit_text("ভিডিও ডাউনলোড হচ্ছে...")
        loop = asyncio.get_event_loop()
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download)

        # ২ জিবি চেক (টেলিগ্রাম বট লিমিট)
        file_size = os.path.getsize(file_path)
        if file_size > 2 * 1024 * 1024 * 1024:
            await msg.edit_text("ভিডিও সাইজ ২ জিবির বেশি, তাই টেলিগ্রামে পাঠানো সম্ভব নয়।")
            os.remove(file_path)
            return

        await msg.edit_text("টেলিগ্রাম গ্রুপে আপলোড করা হচ্ছে...")
        
        # টেলিগ্রামে ভিডিও সেন্ড
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption="ডাউনলোড সম্পন্ন হয়েছে!",
            supports_streaming=True,
            reply_to_message_id=message.id
        )
        # আপলোড শেষ হলে প্রসেসিং মেসেজটি ডিলিট করে দেবে
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"ত্রুটি: {str(e)}")

    finally:
        # এটিই আপনার মূল রিকোয়ারমেন্ট!
        # ভিডিও গ্রুপে যাওয়ার পর লোকাল স্টোরেজ (Railway) থেকে ফাইলটি চিরতরে ডিলিট হয়ে যাবে।
        # তবে ভিডিওটি টেলিগ্রাম গ্রুপে স্থায়ীভাবে থেকে যাবে।
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("বট চালু হচ্ছে...")
    app.run()
