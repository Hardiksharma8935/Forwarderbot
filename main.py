import os
import re
import telebot

# ── Environment Variables ──────────────────────────────────────────────────────
BOT_TOKEN     = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN set nahi hai! Railway → Variables mein add karo.")
if not GROUP_CHAT_ID:
    raise ValueError("❌ GROUP_CHAT_ID set nahi hai! Railway → Variables mein add karo.")

# ── Bot Setup ──────────────────────────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN)

LINK_REGEX = r'(https?://[^\s]+)'

# ── Handlers ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != 'private':
        return
    bot.reply_to(
        message,
        "👋 Hello!\n\nMujhe koi bhi link bhejo, main use group mein forward kar dunga. 🔗"
    )

@bot.message_handler(
    func=lambda m: m.chat.type == 'private' and bool(re.findall(LINK_REGEX, m.text or ''))
)
def handle_link(message):
    links = re.findall(LINK_REGEX, message.text)
    success_count = 0

    for link in links:
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"🔗 <b>New Link Shared</b>\n\n{link}",
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            print(f"❌ Forward error: {e}")

    if success_count == len(links):
        bot.reply_to(message, f"✅ {success_count} link(s) group mein bhej diye!")
    else:
        bot.reply_to(message, "⚠️ Kuch links forward nahi hue. Admin se baat karo.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def handle_other(message):
    bot.reply_to(message, "Sirf links bhejo bhai 🔗\nExample: https://example.com")

# ── Start Polling ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Bot start ho gaya — Polling mode...")
    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        none_stop=True
    )
