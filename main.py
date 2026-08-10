import os
import urllib.parse
import telebot
import google.generativeai as genai

# Railway Environment Variables থেকে কী নেওয়া হবে
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ভ্যারিয়েবল সেট করা হয়নি!")

bot = telebot.TeleBot(BOT_TOKEN)

# Gemini AI কনফিগারেশন
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **AI Generator Bot-এ স্বাগতম!**\n\n"
        "✨ **যেভাবে কমান্ড দেবেন:**\n"
        "🔹 **লেখা জেনারেট করতে:** `/ask আপনার প্রশ্ন`\n"
        "🔹 **ছবি তৈরি করতে:** `/img ছবির বর্ণনা (English)`\n\n"
        "**উদাহরণ:**\n"
        "• `/ask কৃত্রিম বুদ্ধিমত্তা কী এবং এটি কীভাবে কাজ করে?`\n"
        "• `/img A futuristic astronaut riding a horse on Mars, hyperrealistic, 8k resolution`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['ask'])
def handle_ask(message):
    prompt = message.text.replace('/ask', '').strip()
    
    if not prompt:
        bot.reply_to(message, "⚠️ অনুগ্রহ করে কোনো প্রশ্ন লিখুন। যেমন: `/ask কম্পিউটার কী?`", parse_mode="Markdown")
        return

    msg = bot.reply_to(message, "🧠 চিন্তা করছি, একটু অপেক্ষা করুন...")
    
    try:
        if not GEMINI_API_KEY:
            bot.edit_message_text("❌ Gemini API Key পাওয়া যায়নি। Railway Environment Variables চেক করুন।", chat_id=message.chat.id, message_id=msg.message_id)
            return

        response = model.generate_content(prompt)
        bot.edit_message_text(response.text, chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ সমস্যা হয়েছে: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

@bot.message_handler(commands=['img', 'image'])
def handle_image(message):
    prompt = message.text.replace('/img', '').replace('/image', '').strip()
    
    if not prompt:
        bot.reply_to(message, "⚠️ ছবির বর্ণনা (English Prompt) দিন। যেমন: `/img A cute cat wearing glasses reading a book`", parse_mode="Markdown")
        return

    msg = bot.reply_to(message, "🎨 ছবি তৈরি করা হচ্ছে, অপেক্ষা করুন...")
    
    try:
        # Pollinations API দিয়ে ইমেজ জেনারেট করা
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024"
        
        bot.send_photo(
            chat_id=message.chat.id, 
            photo=image_url, 
            caption=f"🖼 **Prompt:** `{prompt}`", 
            parse_mode="Markdown"
        )
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ ছবি তৈরিতে ব্যর্থ হয়েছে: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
