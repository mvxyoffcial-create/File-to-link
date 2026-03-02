# 🔗 FileStreamBot

A powerful Telegram File Stream & Direct Link Generator Bot.

**Developer:** [@Venuboyy](https://t.me/Venuboyy)

---

## ✨ Features
- 📁 Supports ALL file types up to **4GB**
- 🔗 Direct download & streaming links
- 🖥 Built-in **Plyr.js** video player
- 📢 Force subscribe to channels
- ⏰ Links auto-expire in **24 hours**
- 📊 Admin stats & broadcast
- 🗃️ MongoDB database
- 🚀 500 concurrent workers
- 🎞️ Welcome animation sticker
- 🖼️ Random anime wallpaper welcome image
- ℹ️ `/info` command with profile photo

---

## 🔧 Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/FileStreamBot
cd FileStreamBot
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python bot.py
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram Bot Token from @BotFather |
| `API_ID` | ✅ | Telegram API ID from my.telegram.org |
| `API_HASH` | ✅ | Telegram API Hash from my.telegram.org |
| `BIN_CHANNEL` | ✅ | Private channel ID to store files |
| `MONGO_URI` | ✅ | MongoDB connection URI |
| `BASE_URL` | ✅ | Your public server URL (no trailing slash) |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `ADMINS` | ❌ | Space-separated admin IDs |
| `FORCE_SUB_CHANNEL_1` | ❌ | First force-sub channel username |
| `FORCE_SUB_CHANNEL_2` | ❌ | Second force-sub channel username |
| `PORT` | ❌ | Web server port (default: 8080) |
| `WORKERS` | ❌ | Bot workers (default: 500) |
| `LINK_EXPIRY` | ❌ | Link expiry in seconds (default: 86400) |

---

## 📋 Commands

| Command | Access | Description |
|---|---|---|
| `/start` | All | Start the bot |
| `/help` | All | Show help |
| `/about` | All | Bot info |
| `/info` | All | Your Telegram info |
| `/stats` | Admin | Bot statistics |
| `/broadcast` | Admin | Broadcast message (reply to a message) |
| `/cleanup` | Admin | Delete expired file records |

---

## 🚀 Deploy on Heroku

1. Fork this repo
2. Create a new Heroku app
3. Set all environment variables in Heroku Config Vars
4. Deploy via GitHub or Heroku CLI

---

## 📝 Notes
- Bot must be **admin** in BIN_CHANNEL
- Bot must be **admin** in Force Sub channels to check membership
- `BASE_URL` must be your public domain (e.g., `https://mybot.herokuapp.com`)
