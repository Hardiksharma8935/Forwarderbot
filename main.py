import os
import re
import json
import telebot

BOT_TOKEN     = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")
SENT_LINKS_FILE = "sent_links.json"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN set nahi hai!")
if not GROUP_CHAT_ID:
    raise ValueError("❌ GROUP_CHAT_ID set nahi hai!")

bot = telebot.TeleBot(BOT_TOKEN)

# Public link  → t.me/groupname
# Private link → t.me/+XXXX ya t.me/joinchat/XXXX (ignore)
PUBLIC_TG_REGEX  = r'https?://(?:t\.me|telegram\.me)/([a-zA-Z0-9_]{4,})'
PRIVATE_TG_REGEX = r'https?://(?:t\.me|telegram\.me)/(?:\+|joinchat/)[^\s]+'


# ── Duplicate tracking ─────────────────────────────────────────────────────────

def load_sent_links() -> set:
    """File se pehle bheje gaye links load karo"""
    try:
        with open(SENT_LINKS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_sent_links(links: set):
    """Sent links file mein save karo"""
    with open(SENT_LINKS_FILE, "w") as f:
        json.dump(list(links), f)

# Startup pe load karo
sent_links = load_sent_links()
print(f"📋 {len(sent_links)} links pehle se record mein hain.")


# ── Telegram API helper ────────────────────────────────────────────────────────

def get_group_title(username: str):
    """
    Public group/channel ka naam fetch karo.
    Agar user/bot hai ya accessible nahi → None return karo.
    """
    try:
        chat = bot.get_chat(f"@{username}")
        if chat.type in ("group", "supergroup", "channel"):
            return chat.title
        return None
    except Exception as e:
        print(f"⚠️  get_chat failed for @{username}: {e}")
        return None


# ── Startup ────────────────────────────────────────────────────────────────────
print("🔧 Webhook delete kar rahe hain...")
bot.remove_webhook()
print("✅ Webhook deleted. Polling shuru...")


# ── Handlers ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(message):
    if message.chat.type != "private":
        return
    bot.reply_to(
        message,
        "👋 Hello!\n\n"
        "Mujhe kisi Telegram group/channel ka public link bhejo.\n"
        "Main uska naam aur link group mein forward kar dunga. 🔗\n\n"
        "❌ Expired, request-based aur duplicate links ignore ho jayenge."
    )


@bot.message_handler(func=lambda m: m.chat.type == "private" and bool(m.text))
def handle_message(message):
    global sent_links
    text = message.text

    # Private links — seedha ignore
    private_links = re.findall(PRIVATE_TG_REGEX, text)
    public_usernames = re.findall(PUBLIC_TG_REGEX, text)

    sent      = 0
    ignored   = len(private_links)
    duplicate = 0

    for username in public_usernames:
        link = f"https://t.me/{username}"

        # ── Duplicate check ────────────────────────────────────────────────────
        if link in sent_links:
            duplicate += 1
            print(f"🔁 Duplicate skip: {link}")
            continue

        # ── Group naam fetch karo ──────────────────────────────────────────────
        title = get_group_title(username)

        if title is None:
            ignored += 1
            print(f"⏭️  Ignored: @{username}")
            continue

        # ── Group chat mein bhejo ──────────────────────────────────────────────
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"📢 <b>{title}</b>\n🔗 {link}",
                parse_mode="HTML"
            )
            sent_links.add(link)
            save_sent_links(sent_links)   # file mein save karo
            sent += 1
            print(f"✅ Forwarded: {title} → {link}")
        except Exception as e:
            print(f"❌ Send error: {e}")
            ignored += 1

    # ── User ko reply ──────────────────────────────────────────────────────────
    parts = []
    if sent > 0:
        parts.append(f"✅ {sent} group(s) forward ho gaye!")
    if duplicate > 0:
        parts.append(f"🔁 {duplicate} pehle se bheja ja chuka hai, skip kiya.")
    if ignored > 0:
        parts.append(f"⚠️ {ignored} ignore kiye (expired / request-based / invalid).")

    if parts:
        bot.reply_to(message, "\n".join(parts))
    else:
        bot.reply_to(
            message,
            "Koi valid Telegram link nahi mila.\n"
            "Example: https://t.me/groupname"
        )


# ── Start ──────────────────────────────────────────────────────────────────────
print("🤖 Bot chal raha hai...")
bot.infinity_polling(timeout=30, long_polling_timeout=20, none_stop=True)
