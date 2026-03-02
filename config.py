import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Config
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    
    # Owner & Admins
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split() if x]
    
    # Channels
    BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", 0))  # Private storage channel
    FORCE_SUB_CHANNEL_1 = os.environ.get("FORCE_SUB_CHANNEL_1", "zerodev2")
    FORCE_SUB_CHANNEL_2 = os.environ.get("FORCE_SUB_CHANNEL_2", "mvxyoffcail")
    
    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "filestreambot")
    
    # Web Server
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
    PORT = int(os.environ.get("PORT", 8080))
    HOST = os.environ.get("HOST", "0.0.0.0")
    
    # Workers
    WORKERS = int(os.environ.get("WORKERS", 500))
    
    # Link expiry (seconds) - 24 hours
    LINK_EXPIRY = int(os.environ.get("LINK_EXPIRY", 86400))
    
    # Welcome sticker
    WELCOME_STICKER = "CAACAgIAAxkBAAEQZtFpgEdROhGouBVFD3e0K-YjmVHwsgACtCMAAphLKUjeub7NKlvk2TgE"
    
    # Wallpaper API
    WALLPAPER_API = "https://api.aniwallpaper.workers.dev/random?type=girl"
    
    # Dev links
    DEV_LINK = "https://t.me/Venuboyy"
    
    # Bot username (set after bot starts)
    BOT_USERNAME = ""
