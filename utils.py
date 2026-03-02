import math
import logging
import asyncio
import aiohttp
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from config import Config

logger = logging.getLogger(__name__)

def humanbytes(size: int) -> str:
    """Convert bytes to human readable format."""
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    units = {0: 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

async def check_force_sub(client: Client, user_id: int) -> bool:
    """Check if user is subscribed to all required channels."""
    channels = [Config.FORCE_SUB_CHANNEL_1, Config.FORCE_SUB_CHANNEL_2]
    for channel in channels:
        if not channel:
            continue
        try:
            member = await client.get_chat_member(f"@{channel}", user_id)
            if member.status.name in ("BANNED", "LEFT"):
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            logger.warning(f"Force sub check error for @{channel}: {e}")
            # Skip if can't check
            continue
    return True

async def get_random_wallpaper() -> str:
    """Fetch a random wallpaper URL from the API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.WALLPAPER_API, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    # The API may return a redirect or direct image URL
                    return str(resp.url)
    except Exception as e:
        logger.warning(f"Wallpaper API error: {e}")
    return "https://i.ibb.co/pr2H8cwT/img-8312532076.jpg"

def get_file_info(message):
    """Extract file info from a Pyrogram message."""
    for attr in ("document", "video", "audio", "photo", "voice", "video_note", "animation", "sticker"):
        media = getattr(message, attr, None)
        if media:
            file_name = getattr(media, "file_name", None) or f"{attr}_{media.file_unique_id}"
            file_size = getattr(media, "file_size", 0) or 0
            mime_type = getattr(media, "mime_type", "application/octet-stream") or "application/octet-stream"
            return media.file_id, media.file_unique_id, file_name, file_size, mime_type
    return None, None, None, 0, None
