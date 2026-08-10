import os
import urllib.parse
import requests
import telebot
import google.generativeai as genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN পাওয়া যায়নি!")

bot = telebot.TeleBot(BOT_TOKEN)

# Gemini AI সেটআপ
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
        "• `/ask বাংলাদেশের ইতিহাস সংক্ষেপে বলো`\n"
        "• `/img A cute cat driving a car, 4k`"
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
            bot.edit_message_text("❌ Gemini API Key পাওয়া যায়নি। Railway তে GEMINI_API_KEY ঠিক করুন।", chat_id=message.chat.id, message_id=msg.message_id)
            return

        response = model.generate_content(prompt)
        bot.edit_message_text(response.text, chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Gemini API সমস্যা হয়েছে: {str(e)}\n\n💡 নিশ্চিত করুন আপনার API Key-টি 'AIzaSy' দিয়ে শুরু হয়েছে কিনা।", chat_id=message.chat.id, message_id=msg.message_id)

@bot.message_handler(commands=['img', 'image'])
def handle_image(message):
    prompt = message.text.replace('/img', '').replace('/image', '').strip()
    
    if not prompt:
        bot.reply_to(message, "⚠️ ছবির বর্ণনা (English Prompt) দিন। যেমন: `/img A cute cat`", parse_mode="Markdown")
        return

    msg = bot.reply_to(message, "🎨 ছবি তৈরি করা হচ্ছে, অপেক্ষা করুন...")
    
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        # সঠিক Pollinations Direct Image Endpoint
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        # সরাসরি ছবি ডাউনলোড করে বাইট আকারে পাঠানো
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            bot.send_photo(
                chat_id=message.chat.id, 
                photo=response.content, 
                caption=f"🖼 **Prompt:** `{prompt}`", 
                parse_mode="Markdown"
            )
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ ছবি জেনারেট করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।", chat_id=message.chat.id, message_id=msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ সমস্যা হয়েছে: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
