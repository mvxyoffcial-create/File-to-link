import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Config
    BOT_TOKEN = "8731151889:AAGHWDNuYdAOOj2PyUwtyXVt8loyzCkwsCU"
    API_ID = 20288994
    API_HASH = "d702614912f1ad370a0d18786002adbf"
    
    # Owner & Admins
    OWNER_ID = 8498741978
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split() if x]
    
    # Channels
    BIN_CHANNEL = -1003853860662  # Private storage channel
    FORCE_SUB_CHANNEL_1 = "zerodev2"
    FORCE_SUB_CHANNEL_2 = "mvxyoffcail"
    
    # MongoDB
    MONGO_URI = "mongodb+srv://Zerobothost:zero8907@cluster0.szwdcyb.mongodb.net/?appName=Cluster07"
    DATABASE_NAME = "filestreambot"
    
    # Web Server
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
    PORT = 8080
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
