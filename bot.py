"""
FileStreamBot - Main Entry Point
Developer: @Venuboyy
"""
import asyncio
import logging
import sys
from pyrogram import Client
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters

from config import Config
from web_server import start_web_server
from bot.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting FileStreamBot...")

    app = Client(
        name="FileStreamBot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        workers=Config.WORKERS,
        sleep_threshold=60,
        max_concurrent_transmissions=500,
    )

    # Register all handlers
    register_handlers(app)

    await app.start()

    # Set bot username
    me = await app.get_me()
    Config.BOT_USERNAME = me.username
    logger.info(f"Bot started as @{me.username}")

    # Validate BIN_CHANNEL
    try:
        chat = await app.get_chat(Config.BIN_CHANNEL)
        logger.info(f"BIN_CHANNEL OK: {chat.title} ({chat.id})")
    except Exception as e:
        logger.critical(
            f"\n\n❌ BIN_CHANNEL ERROR: {e}"
            f"\n   BIN_CHANNEL = {Config.BIN_CHANNEL}"
            f"\n   Fix: Make sure the ID starts with -100 and bot is admin."
            f"\n   Get correct ID: forward any channel message to @userinfobot\n"
        )

    # Start web server
    runner = await start_web_server(app)
    logger.info(f"Web server running at {Config.BASE_URL}")

    logger.info("FileStreamBot is fully online! 🚀")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("Shutting down...")
        await runner.cleanup()
        await app.stop()
        logger.info("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
