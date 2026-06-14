# Telegram Link Forwarder Bot 🔗

Telegram bot jo private chat mein aaye links automatically group mein forward karta hai.

## Railway pe Deploy Kaise Karein

### Step 1 — Environment Variables Set Karo
Railway dashboard → apna project → Variables tab mein ye do variables add karo:

| Variable | Value |
|----------|-------|
| `BOT_TOKEN` | BotFather se mila token |
| `GROUP_CHAT_ID` | Group ka ID (jaise `-1001234567890`) |

### Step 2 — Deploy
Railway GitHub se auto-deploy kar dega. Bas commit karo!

## GROUP_CHAT_ID Kaise Pata Kare?

1. [@userinfobot](https://t.me/userinfobot) ko group mein add karo
2. Woh group ID bata dega (usually `-100` se shuru hota hai)

## Bot Features
- ✅ Private chat mein link bhejo → group mein forward
- ✅ `/start` command support
- ✅ Auto-restart on crash (`none_stop=True`)
- ✅ Multiple links ek saath handle karta hai
