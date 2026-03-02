import asyncio
import logging
import time
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import Config
from script import Script
from database import (
    add_user, get_user_count, get_file_count, get_all_users,
    save_file, get_file, delete_expired_files
)
from utils import humanbytes, check_force_sub, get_random_wallpaper, get_file_info

logger = logging.getLogger(__name__)


# ─── URL helpers ──────────────────────────────────────────────────────────────
def get_base_url() -> str:
    url = (Config.BASE_URL or "").strip().rstrip("/")
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return ""

def make_file_buttons(file_db_id: str, include_stream: bool = False) -> InlineKeyboardMarkup:
    base = get_base_url()
    bot_user = Config.BOT_USERNAME or ""
    rows = []

    if base:
        label = "🖥 Stream ↗" if include_stream else "🖥 Watch ↗"
        rows.append([
            InlineKeyboardButton("📥 Download ↗", url=f"{base}/dl/{file_db_id}"),
            InlineKeyboardButton(label, url=f"{base}/watch/{file_db_id}"),
        ])

    rows.append([
        InlineKeyboardButton("🔗 Get File", callback_data=f"getfile_{file_db_id}"),
        InlineKeyboardButton("❌ Revoke",   callback_data=f"revoke_{file_db_id}"),
    ])
    rows.append([InlineKeyboardButton("🚫 Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)

def make_link_text(file_name: str, file_size: str, file_db_id: str) -> str:
    base     = get_base_url()
    bot_user = Config.BOT_USERNAME or ""
    dl_url    = f"{base}/dl/{file_db_id}"    if base     else "Set BASE_URL env var"
    watch_url = f"{base}/watch/{file_db_id}" if base     else "Set BASE_URL env var"
    share_url = f"https://t.me/{bot_user}?start=file_{file_db_id}" if bot_user else "N/A"
    return Script.LINK_TXT.format(
        file_name=file_name, file_size=file_size,
        download_url=dl_url, watch_url=watch_url, share_url=share_url,
    )


# ─── /start ──────────────────────────────────────────────────────────────────
async def start_handler(client: Client, message: Message):
    user = message.from_user
    await add_user(user.id, user.first_name, user.username)

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("file_"):
        await send_file_links(client, message, args[1][5:])
        return

    if not await check_force_sub(client, user.id):
        await send_force_sub(message)
        return

    try:
        sticker_msg = await message.reply_sticker(Config.WELCOME_STICKER, quote=True)
        await asyncio.sleep(2)
        await sticker_msg.delete()
    except Exception as e:
        logger.warning(f"Sticker error: {e}")

    me = await client.get_me()
    Config.BOT_USERNAME = me.username or ""

    img_url = await get_random_wallpaper()

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Help", callback_data="help"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Venuboyy")],
    ])

    try:
        await message.reply_photo(photo=img_url,
            caption=Script.START_TXT.format(user.mention, "👋"),
            reply_markup=buttons, quote=True)
    except Exception:
        await message.reply_text(Script.START_TXT.format(user.mention, "👋"),
            reply_markup=buttons, quote=True)


# ─── Force Sub ───────────────────────────────────────────────────────────────
async def send_force_sub(message: Message):
    ch1, ch2 = Config.FORCE_SUB_CHANNEL_1, Config.FORCE_SUB_CHANNEL_2
    rows = []
    if ch1 and ch2:
        rows.append([
            InlineKeyboardButton("📢 Channel 1", url=f"https://t.me/{ch1}"),
            InlineKeyboardButton("📢 Channel 2", url=f"https://t.me/{ch2}"),
        ])
    elif ch1:
        rows.append([InlineKeyboardButton("📢 Channel", url=f"https://t.me/{ch1}")])
    elif ch2:
        rows.append([InlineKeyboardButton("📢 Channel", url=f"https://t.me/{ch2}")])
    rows.append([InlineKeyboardButton("✅ Try Again", callback_data="check_sub")])
    await message.reply_text(Script.FORCE_SUB_TXT,
        reply_markup=InlineKeyboardMarkup(rows), quote=True)


# ─── File links ───────────────────────────────────────────────────────────────
async def send_file_links(client: Client, message: Message, file_db_id: str):
    file_doc = await get_file(file_db_id)
    if not file_doc:
        await message.reply_text("❌ File not found or link has expired!", quote=True)
        return
    if time.time() > file_doc.get("expires_at", 0):
        await message.reply_text("⏰ This link has expired!", quote=True)
        return
    await message.reply_text(
        make_link_text(file_doc["file_name"], humanbytes(file_doc["file_size"]), file_db_id),
        reply_markup=make_file_buttons(file_db_id),
        quote=True, disable_web_page_preview=True)


# ─── File receive ─────────────────────────────────────────────────────────────
async def file_handler(client: Client, message: Message):
    user = message.from_user
    if not await check_force_sub(client, user.id):
        await send_force_sub(message)
        return

    await add_user(user.id, user.first_name, user.username)
    processing = await message.reply_text("⏳ **Processing your file...**", quote=True)

    file_id, file_unique_id, file_name, file_size, mime_type = get_file_info(message)
    if not file_id:
        await processing.edit_text("❌ Unsupported file type!")
        return

    try:
        forwarded = await client.forward_messages(
            chat_id=Config.BIN_CHANNEL,
            from_chat_id=message.chat.id,
            message_ids=message.id)
        msg_id = forwarded.id
    except Exception as e:
        logger.error(f"Forward error: {e}")
        await processing.edit_text(f"❌ Failed to store file.\n`{e}`")
        return

    file_db_id = await save_file(
        file_id, file_unique_id, file_name,
        file_size, mime_type, msg_id, user.id)

    await processing.delete()
    await message.reply_text(
        make_link_text(file_name, humanbytes(file_size), file_db_id),
        reply_markup=make_file_buttons(file_db_id, include_stream=True),
        quote=True, disable_web_page_preview=True)


# ─── /info ────────────────────────────────────────────────────────────────────
async def info_handler(client: Client, message: Message):
    user = message.from_user if not message.reply_to_message else message.reply_to_message.from_user
    last_name = user.last_name or "None"
    username  = f"@{user.username}" if user.username else "None"
    dc_id = "Unknown"
    try:
        full  = await client.get_chat(user.id)
        dc_id = getattr(full, "dc_id", "Unknown")
    except Exception:
        pass

    profile_url = f"https://t.me/{user.username}" if user.username else "https://t.me/Venuboyy"
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("👤 Profile Link", url=profile_url)]])
    info_text = Script.INFO_TXT.format(
        first_name=user.first_name, last_name=last_name,
        user_id=user.id, dc_id=dc_id, username=username)

    try:
        photos = await client.get_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            await message.reply_photo(photo=photos[0].file_id,
                caption=info_text, reply_markup=buttons, quote=True)
            return
    except Exception:
        pass
    await message.reply_text(info_text, reply_markup=buttons, quote=True)


# ─── /stats (admin) ───────────────────────────────────────────────────────────
async def stats_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized!", quote=True)
        return
    users = await get_user_count()
    files = await get_file_count()
    await message.reply_text(Script.STATS_TXT.format(users=users, files=files), quote=True)


# ─── /broadcast (admin) ───────────────────────────────────────────────────────
async def broadcast_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ You are not authorized!", quote=True)
        return
    if not message.reply_to_message:
        await message.reply_text("📢 Reply to a message to broadcast it.", quote=True)
        return

    broadcast_msg = message.reply_to_message
    users = await get_all_users()
    total = len(users)
    success, failed = 0, 0
    status_msg = await message.reply_text(f"📢 Broadcasting to {total} users...", quote=True)

    for user in users:
        try:
            await broadcast_msg.copy(user["user_id"])
            success += 1
        except (UserIsBlocked, InputUserDeactivated):
            failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await broadcast_msg.copy(user["user_id"])
                success += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        Script.BROADCAST_TXT.format(success=success, failed=failed, total=total))


# ─── /cleanup (admin) ─────────────────────────────────────────────────────────
async def cleanup_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        return
    deleted = await delete_expired_files()
    await message.reply_text(f"✅ Cleaned up {deleted} expired file records.", quote=True)


# ─── /help ────────────────────────────────────────────────────────────────────
async def help_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])
    await message.reply_text(Script.HELP_TXT, reply_markup=buttons, quote=True)


# ─── /about ───────────────────────────────────────────────────────────────────
async def about_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="start"),
         InlineKeyboardButton("📚 Help", callback_data="help")]
    ])
    bot_user = Config.BOT_USERNAME or "FileStreamBot"
    await message.reply_text(
        Script.ABOUT_TXT.format(bot_user, "FileStreamBot"),
        reply_markup=buttons, quote=True, disable_web_page_preview=True)


# ─── Callbacks ────────────────────────────────────────────────────────────────
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user = query.from_user

    if data == "check_sub":
        if await check_force_sub(client, user.id):
            await query.message.delete()
            await query.message.reply_text(
                Script.START_TXT.format(user.mention, "👋"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📚 Help",  callback_data="help"),
                     InlineKeyboardButton("ℹ️ About", callback_data="about")]
                ]))
        else:
            await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
            return

    elif data == "help":
        await query.message.edit_text(Script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home",  callback_data="start"),
                 InlineKeyboardButton("ℹ️ About", callback_data="about")]
            ]))

    elif data == "about":
        bot_user = Config.BOT_USERNAME or "FileStreamBot"
        await query.message.edit_text(
            Script.ABOUT_TXT.format(bot_user, "FileStreamBot"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="start"),
                 InlineKeyboardButton("📚 Help", callback_data="help")]
            ]), disable_web_page_preview=True)

    elif data == "start":
        await query.message.edit_text(
            Script.START_TXT.format(user.mention, "👋"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Help",  callback_data="help"),
                 InlineKeyboardButton("ℹ️ About", callback_data="about")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Venuboyy")],
            ]))

    elif data == "close":
        await query.message.delete()

    elif data.startswith("revoke_"):
        file_db_id = data[7:]
        from database import files_col
        from bson import ObjectId
        try:
            await files_col.delete_one({"_id": ObjectId(file_db_id)})
            await query.message.edit_text("✅ File link has been revoked successfully!")
        except Exception:
            await query.answer("❌ Failed to revoke file.", show_alert=True)
            return

    elif data.startswith("getfile_"):
        file_db_id = data[8:]
        file_doc = await get_file(file_db_id)
        if not file_doc:
            await query.answer("❌ File not found or expired!", show_alert=True)
            return
        if time.time() > file_doc.get("expires_at", 0):
            await query.answer("⏰ This link has expired!", show_alert=True)
            return
        try:
            await client.copy_message(
                chat_id=user.id,
                from_chat_id=Config.BIN_CHANNEL,
                message_id=file_doc["message_id"])
            await query.answer("✅ File sent to your DM!", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)
            return

    await query.answer()


# ─── Register ─────────────────────────────────────────────────────────────────
def register_handlers(app: Client):
    from pyrogram.handlers import MessageHandler, CallbackQueryHandler

    app.add_handler(MessageHandler(start_handler,     filters.command("start") & filters.private))
    app.add_handler(MessageHandler(help_handler,      filters.command("help")))
    app.add_handler(MessageHandler(about_handler,     filters.command("about")))
    app.add_handler(MessageHandler(info_handler,      filters.command("info")))
    app.add_handler(MessageHandler(stats_handler,     filters.command("stats")))
    app.add_handler(MessageHandler(broadcast_handler, filters.command("broadcast")))
    app.add_handler(MessageHandler(cleanup_handler,   filters.command("cleanup")))
    app.add_handler(MessageHandler(file_handler,
        filters.private & (
            filters.document | filters.video | filters.audio |
            filters.photo    | filters.voice | filters.video_note |
            filters.animation)))
    app.add_handler(CallbackQueryHandler(callback_handler))
