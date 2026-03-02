from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import time

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client[Config.DATABASE_NAME]

users_col = db["users"]
files_col = db["files"]

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
                    uploader_id: int):
    doc = {
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "file_name": file_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "message_id": message_id,
        "uploader_id": uploader_id,
        "created_at": int(time.time()),
        "expires_at": int(time.time()) + Config.LINK_EXPIRY
    }
    result = await files_col.insert_one(doc)
    return str(result.inserted_id)

async def get_file(file_db_id: str):
    from bson import ObjectId
    try:
        doc = await files_col.find_one({"_id": ObjectId(file_db_id)})
        return doc
    except Exception:
        return None

async def delete_expired_files():
    now = int(time.time())
    result = await files_col.delete_many({"expires_at": {"$lt": now}})
    return result.deleted_count

async def get_file_count():
    return await files_col.count_documents({})
