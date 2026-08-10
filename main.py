import os
import time
import threading
from telebot import TeleBot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

# যে গ্রুপে বা চ্যানেলে মেসেজ পাঠাবে তার Chat ID (উদাহরণস্বরূপ: -100xxxxxxxxxx)
# আপনি চাইলে গ্রুপে /start লিখে চ্যাট আইডি বের করতে পারেন বা এখানে সরাসরি আইডি বসাতে পারেন।
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID") 

# যে মেসেজটি বারবার পাঠাবে
MESSAGE_TEXT = "🤖 এই মেসেজটি স্বয়ংক্রিয়ভাবে বারবার পাঠানো হচ্ছে! (Auto-posting bot active)"

def auto_poster():
    """ব্যাকগ্রাউন্ডে নির্দিষ্ট সময় পর পর মেসেজ পাঠাতে থাকবে"""
    while True:
        try:
            if GROUP_CHAT_ID:
                bot.send_message(chat_id=int(GROUP_CHAT_ID), text=MESSAGE_TEXT)
            # এখানে সময় সেট করা আছে (যেমন: ৩ সেকেন্ড পর পর)
            time.sleep(3) 
        except Exception as e:
            print(f"Error sending message: {e}")
            time.sleep(5) # কোনো সমস্যা হলে ৫ সেকেন্ড অপেক্ষা করে আবার চেষ্টা করবে

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.reply_to(
        message, 
        f"✅ অটো-মেসেজ বট চালু হয়েছে!\nআপনার এই গ্রুপের Chat ID হলো: `{chat_id}`\n\nএই আইডিটি Railway-এর Variables-এ `GROUP_CHAT_ID` হিসেবে সেট করে দিন।",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে মেসেজ পাঠানোর জন্য আলাদা একটি Thread চালু করা হলো
    poster_thread = threading.Thread(target=auto_poster, daemon=True)
    poster_thread.start()
    
    print("Auto Poster Bot is Running...")
    bot.infinity_polling()
