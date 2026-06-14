import os
import re
import json
import requests
from bs4 import BeautifulSoup
import telebot

BOT_TOKEN       = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID   = os.environ.get("GROUP_CHAT_ID")
SENT_LINKS_FILE = "sent_links.json"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN set nahi hai!")
if not GROUP_CHAT_ID:
    raise ValueError("❌ GROUP_CHAT_ID set nahi hai!")

bot = telebot.TeleBot(BOT_TOKEN)

# Koi bhi t.me link (public ya private)
TG_LINK_REGEX = r'(https?://(?:t\.me|telegram\.me)/[^\s]+)'

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ── Link ka naam fetch karo ────────────────────────────────────────────────────

def get_tg_title(url: str):
    """
    t.me preview page se group/channel naam nikalo.
    - Valid link   → naam (string) return karo
    - Expired link → None return karo
    """
    try:
        r = requests.get(url, headers=SCRAPE_HEADERS, timeout=8)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # ── Expired / invalid check ────────────────────────────────────────────
        # Telegram expired links pe yeh class hoti hai
        desc = soup.find("div", class_="tgme_page_description")
        if desc and any(x in desc.text.lower() for x in
                        ["no longer valid", "invalid", "expired", "link is not valid"]):
            return None

        # ── Naam nikalo ────────────────────────────────────────────────────────
        # Method 1: og:title meta tag (sabse reliable)
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content") and og["content"].lower() != "telegram":
            return og["content"].strip()

        # Method 2: tgme_page_title div (fallback)
        title_div = soup.find("div", class_="tgme_page_title")
        if title_div:
            span = title_div.find("span")
            if span and span.text.strip():
                return span.text.strip()

        return None

    except Exception as e:
        print(f"⚠️  Scrape error [{url}]: {e}")
        return None


# ── Duplicate tracking ─────────────────────────────────────────────────────────

def load_sent_links() -> set:
    try:
        with open(SENT_LINKS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_sent_links(links: set):
    with open(SENT_LINKS_FILE, "w") as f:
        json.dump(list(links), f)

sent_links = load_sent_links()
print(f"📋 {len(sent_links)} links pehle se record mein hain.")


# ── Startup ────────────────────────────────────────────────────────────────────
print("🔧 Webhook delete kar rahe hain...")
bot.remove_webhook()
print("✅ Polling shuru...")


# ── Handlers ───────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(message):
    if message.chat.type != "private":
        return
    bot.reply_to(
        message,
        "👋 Hello!\n\n"
        "Telegram group/channel ka koi bhi link bhejo — public ya private.\n"
        "Main uska naam aur link group mein forward kar dunga. 🔗\n\n"
        "❌ Expired aur duplicate links ignore ho jayenge."
    )


@bot.message_handler(func=lambda m: m.chat.type == "private" and bool(m.text))
def handle_message(message):
    global sent_links
    text = message.text

    all_links = re.findall(TG_LINK_REGEX, text)

    if not all_links:
        bot.reply_to(message, "Koi Telegram link nahi mila.\nExample: https://t.me/groupname")
        return

    sent      = 0
    expired   = 0
    duplicate = 0

    for url in all_links:

        # ── Duplicate check ────────────────────────────────────────────────────
        if url in sent_links:
            duplicate += 1
            print(f"🔁 Duplicate skip: {url}")
            continue

        # ── Naam fetch karo ────────────────────────────────────────────────────
        title = get_tg_title(url)

        if title is None:
            expired += 1
            print(f"⏭️  Expired/invalid: {url}")
            continue

        # ── Group mein bhejo ───────────────────────────────────────────────────
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                f"📢 <b>{title}</b>\n🔗 {url}",
                parse_mode="HTML"
            )
            sent_links.add(url)
            save_sent_links(sent_links)
            sent += 1
            print(f"✅ Forwarded: {title}")
        except Exception as e:
            print(f"❌ Send error: {e}")

    # ── User ko reply ──────────────────────────────────────────────────────────
    parts = []
    if sent:
        parts.append(f"✅ {sent} link(s) forward ho gaye!")
    if duplicate:
        parts.append(f"🔁 {duplicate} pehle se bhej chuke hain, skip kiya.")
    if expired:
        parts.append(f"⚠️ {expired} expired ya invalid hain, ignore kiya.")

    bot.reply_to(message, "\n".join(parts) if parts else "Kuch nahi hua.")


# ── Start ──────────────────────────────────────────────────────────────────────
print("🤖 Bot chal raha hai...")
bot.infinity_polling(timeout=30, long_polling_timeout=20, none_stop=True)
