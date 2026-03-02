from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import time
import hashlib
import base64

client_db = AsyncIOMotorClient(Config.MONGO_URI)
db = client_db[Config.DATABASE_NAME]

users_col = db["users"]
files_col = db["files"]


# ─── Hash helper ──────────────────────────────────────────
def make_hash(file_unique_id: str) -> str:
    """
    Create a short, URL-safe hash from file_unique_id.
    Uses first 8 bytes of SHA256 → base64url → ~11 chars.
    Example: AgAD8yXk3Qw  (looks like Telegram file_unique_id)
    """
    raw = hashlib.sha256(file_unique_id.encode()).digest()[:8]
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


# ─── Users ───────────────────────────────────────────────
async def add_user(user_id: int, first_name: str, username: str = None):
    existing = await users_col.find_one({"user_id": user_id})
    if not existing:
        await users_col.insert_one({
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "joined": int(time.time())
        })

async def get_all_users():
    return await users_col.find().to_list(length=None)

async def get_user_count():
    return await users_col.count_documents({})

async def is_user_exist(user_id: int):
    return bool(await users_col.find_one({"user_id": user_id}))


# ─── Files ───────────────────────────────────────────────
async def save_file(file_id: str, file_unique_id: str, file_name: str,
                    file_size: int, mime_type: str, message_id: int,
                    uploader_id: int, permanent: bool = False):
    """
    Save file. Returns (hash, is_new).
    If a file with the same file_unique_id already exists, return existing hash.
    permanent=True  → expires_at = year 2224 (200 years)
    permanent=False → expires_at = now + LINK_EXPIRY (24h)
    """
    file_hash = make_hash(file_unique_id)

    # Check if already stored
    existing = await files_col.find_one({"hash": file_hash})
    if existing:
        return file_hash, False

    # 200 years in seconds = 200 * 365.25 * 86400 ≈ 6,311,390,400
    PERMANENT_EXPIRY = int(time.time()) + 6_311_390_400

    doc = {
        "hash": file_hash,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "file_name": file_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "message_id": message_id,
        "uploader_id": uploader_id,
        "created_at": int(time.time()),
        "expires_at": PERMANENT_EXPIRY if permanent else int(time.time()) + Config.LINK_EXPIRY,
        "permanent": permanent,
    }
    await files_col.insert_one(doc)
    return file_hash, True


async def get_file_by_hash(file_hash: str):
    """Lookup file by its short hash."""
    return await files_col.find_one({"hash": file_hash})


async def delete_expired_files():
    now = int(time.time())
    result = await files_col.delete_many({
        "expires_at": {"$lt": now},
        "permanent": False
    })
    return result.deleted_count


async def get_file_count():
    return await files_col.count_documents({})


async def get_permanent_count():
    return await files_col.count_documents({"permanent": True})


async def get_temp_count():
    return await files_col.count_documents({"permanent": False})
