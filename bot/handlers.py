import asyncio
import logging
import math
import time
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import Config
from script import Script
from database import (
    add_user, get_user_count, get_file_count, get_all_users,
    get_permanent_count, get_temp_count,
    save_file, get_file_by_hash, delete_expired_files,
    get_user_files, get_user_file_count, delete_file_by_hash
)
from utils import humanbytes, check_force_sub, get_random_wallpaper, get_file_info

logger = logging.getLogger(__name__)

# Pending uploads: user_id → file info dict (before link type chosen)
pending_uploads: dict = {}

FILES_PER_PAGE = 10


# ─── URL helpers ──────────────────────────────────────────────────────────────
def get_base_url() -> str:
    url = (Config.BASE_URL or "").strip().rstrip("/")
    return url if (url.startswith("http://") or url.startswith("https://")) else ""


def build_urls(file_name: str, file_hash: str):
    base      = get_base_url()
    bot_user  = Config.BOT_USERNAME or ""
    safe_name = urllib.parse.quote(file_name, safe=".-_[]()!")
    if base:
        dl_url    = f"{base}/{safe_name}?hash={file_hash}"
        watch_url = f"{base}/watch/{safe_name}?hash={file_hash}"
    else:
        dl_url    = f"(Set BASE_URL)/{safe_name}?hash={file_hash}"
        watch_url = f"(Set BASE_URL)/watch/{safe_name}?hash={file_hash}"
    share_url = f"https://t.me/{bot_user}?start={file_hash}" if bot_user else f"hash={file_hash}"
    return dl_url, watch_url, share_url


def build_link_message(file_name: str, file_size: str, file_hash: str, permanent: bool) -> str:
    dl_url, watch_url, share_url = build_urls(file_name, file_hash)
    badge       = "🔒 Pᴇʀᴍᴀɴᴇɴᴛ" if permanent else "⏰ 24ʜʀ"
    expiry_note = (
        "♾️ <b>ᴛʜɪs ʟɪɴᴋ ɪs ᴘᴇʀᴍᴀɴᴇɴᴛ ᴀɴᴅ ᴡɪʟʟ ɴᴇᴠᴇʀ ᴇxᴘɪʀᴇ! 🔒</b>"
        if permanent else
        "⚠️ <b>ʟɪɴᴋ ᴡɪʟʟ ᴇxᴘɪʀᴇ ɪɴ 𝟤𝟦ʜʀꜱ 😊</b>"
    )
    return Script.LINK_TXT.format(
        badge=badge, file_name=file_name, file_size=file_size,
        download_url=dl_url, watch_url=watch_url,
        share_url=share_url, expiry_note=expiry_note,
    )


def build_file_buttons(file_hash: str, permanent: bool) -> InlineKeyboardMarkup:
    base = get_base_url()
    rows = []
    if base:
        safe = urllib.parse.quote("file", safe="")
        rows.append([
            InlineKeyboardButton("📥 Dᴏᴡɴʟᴏᴀᴅ ↗", url=f"{base}/?hash={file_hash}"),
            InlineKeyboardButton("🖥 Sᴛʀᴇᴀᴍ ↗",   url=f"{base}/watch/?hash={file_hash}"),
        ])
    rows.append([
        InlineKeyboardButton("🔗 Gᴇᴛ Fɪʟᴇ", callback_data=f"getfile_{file_hash}"),
        InlineKeyboardButton("❌ Rᴇᴠᴏᴋᴇ",   callback_data=f"revoke_{file_hash}"),
    ])
    rows.append([InlineKeyboardButton("🚫 Cʟᴏꜱᴇ", callback_data="close")])
    return InlineKeyboardMarkup(rows)


# ─── /files list builder ──────────────────────────────────────────────────────
def truncate(text: str, max_len: int = 28) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


async def build_files_page(user_id: int, page: int):
    """Returns (text, InlineKeyboardMarkup) for the /files page."""
    total    = await get_user_file_count(user_id)
    pages    = max(1, math.ceil(total / FILES_PER_PAGE))
    page     = max(0, min(page, pages - 1))
    files    = await get_user_files(user_id, page, FILES_PER_PAGE)

    if not files:
        return "📂 <b>You have no uploaded files yet.</b>", None

    start_n = page * FILES_PER_PAGE + 1
    lines   = [f"<b>📂 Yᴏᴜʀ Fɪʟᴇs — Pᴀɢᴇ {page+1}/{pages}</b>\n"]
    rows    = []

    for i, f in enumerate(files):
        n         = start_n + i
        badge     = "🔒" if f.get("permanent") else "⏰"
        size_str  = humanbytes(f["file_size"])
        name      = truncate(f["file_name"])
        lines.append(f"{n}. {badge} <code>{name}</code>  <i>{size_str}</i>")
        # Each file gets its own button row
        rows.append([InlineKeyboardButton(
            f"{n}. {badge} {truncate(f['file_name'], 30)}",
            callback_data=f"filedetail_{f['hash']}"
        )])

    # Pagination nav
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Pʀᴇᴠ", callback_data=f"filespage_{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton("Nᴇxᴛ ▶️", callback_data=f"filespage_{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🚫 Cʟᴏꜱᴇ", callback_data="close")])

    text = "\n".join(lines)
    return text, InlineKeyboardMarkup(rows)


async def build_file_detail(file_hash: str, user_id: int):
    """Returns (text, markup) for a single file detail view."""
    doc = await get_file_by_hash(file_hash)
    if not doc:
        return "❌ File not found or expired.", None

    dl_url, watch_url, share_url = build_urls(doc["file_name"], file_hash)
    permanent = doc.get("permanent", False)
    badge     = "🔒 Pᴇʀᴍᴀɴᴇɴᴛ" if permanent else "⏰ 24ʜʀ"

    expiry_note = (
        "♾️ Never expires"
        if permanent else
        f"⏰ Expires: <code>{time.strftime('%Y-%m-%d %H:%M', time.gmtime(doc['expires_at']))}</code> UTC"
    )

    text = (
        f"<b>📂 Fɪʟᴇ Dᴇᴛᴀɪʟs {badge}</b>\n\n"
        f"📄 <b>Name:</b> <code>{doc['file_name']}</code>\n"
        f"📦 <b>Size:</b> <code>{humanbytes(doc['file_size'])}</code>\n"
        f"🗂 <b>Type:</b> <code>{doc.get('mime_type','—')}</code>\n"
        f"{expiry_note}\n\n"
        f"📥 <b>Download:</b>\n<code>{dl_url}</code>\n\n"
        f"🖥 <b>Watch:</b>\n<code>{watch_url}</code>\n\n"
        f"🔗 <b>Share:</b>\n<code>{share_url}</code>"
    )

    base = get_base_url()
    rows = []
    if base:
        rows.append([
            InlineKeyboardButton("📥 Dᴏᴡɴʟᴏᴀᴅ ↗", url=dl_url),
            InlineKeyboardButton("🖥 Wᴀᴛᴄʜ ↗",    url=watch_url),
        ])
    rows.append([
        InlineKeyboardButton("🔗 Gᴇᴛ Fɪʟᴇ",    callback_data=f"getfile_{file_hash}"),
        InlineKeyboardButton("🗑 Rᴇᴠᴏᴋᴇ Fɪʟᴇ", callback_data=f"myrevoke_{file_hash}"),
    ])
    rows.append([InlineKeyboardButton("◀️ Bᴀᴄᴋ ᴛᴏ Lɪsᴛ", callback_data="filespage_0")])
    return text, InlineKeyboardMarkup(rows)


# ─── /start ───────────────────────────────────────────────────────────────────
async def start_handler(client: Client, message: Message):
    user = message.from_user
    await add_user(user.id, user.first_name, user.username)

    args = message.text.split()
    if len(args) > 1:
        file_hash = args[1]
        if file_hash.startswith("file_"):
            file_hash = file_hash[5:]
        await send_file_by_hash(client, message, file_hash)
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
        [InlineKeyboardButton("📚 Hᴇʟᴘ",  callback_data="help"),
         InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about")],
        [InlineKeyboardButton("👨‍💻 Dᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/Venuboyy")],
    ])
    try:
        await message.reply_photo(photo=img_url,
            caption=Script.START_TXT.format(user.mention, "👋"),
            reply_markup=buttons, quote=True)
    except Exception:
        await message.reply_text(Script.START_TXT.format(user.mention, "👋"),
            reply_markup=buttons, quote=True)


# ─── Force Sub ────────────────────────────────────────────────────────────────
async def send_force_sub(message: Message):
    ch1, ch2 = Config.FORCE_SUB_CHANNEL_1, Config.FORCE_SUB_CHANNEL_2
    rows = []
    if ch1 and ch2:
        rows.append([
            InlineKeyboardButton("📢 Cʜᴀɴɴᴇʟ 1", url=f"https://t.me/{ch1}"),
            InlineKeyboardButton("📢 Cʜᴀɴɴᴇʟ 2", url=f"https://t.me/{ch2}"),
        ])
    elif ch1:
        rows.append([InlineKeyboardButton("📢 Cʜᴀɴɴᴇʟ", url=f"https://t.me/{ch1}")])
    elif ch2:
        rows.append([InlineKeyboardButton("📢 Cʜᴀɴɴᴇʟ", url=f"https://t.me/{ch2}")])
    rows.append([InlineKeyboardButton("✅ Tʀʏ Aɢᴀɪɴ", callback_data="check_sub")])
    await message.reply_text(Script.FORCE_SUB_TXT,
        reply_markup=InlineKeyboardMarkup(rows), quote=True)


# ─── Send file by hash ────────────────────────────────────────────────────────
async def send_file_by_hash(client: Client, message: Message, file_hash: str):
    doc = await get_file_by_hash(file_hash)
    if not doc:
        await message.reply_text("❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ ᴏʀ ʟɪɴᴋ ʜᴀs ᴇxᴘɪʀᴇᴅ!", quote=True)
        return
    if not doc.get("permanent") and time.time() > doc.get("expires_at", 0):
        await message.reply_text("⏰ Tʜɪs ʟɪɴᴋ ʜᴀs ᴇxᴘɪʀᴇᴅ!", quote=True)
        return
    await message.reply_text(
        build_link_message(doc["file_name"], humanbytes(doc["file_size"]),
                           file_hash, doc.get("permanent", False)),
        reply_markup=build_file_buttons(file_hash, doc.get("permanent", False)),
        quote=True, disable_web_page_preview=True)


# ─── /files command ───────────────────────────────────────────────────────────
async def files_handler(client: Client, message: Message):
    user = message.from_user
    text, markup = await build_files_page(user.id, 0)
    if markup is None:
        await message.reply_text(text, quote=True)
    else:
        await message.reply_text(text, reply_markup=markup, quote=True)


# ─── File receive ─────────────────────────────────────────────────────────────
async def file_handler(client: Client, message: Message):
    user = message.from_user
    if not await check_force_sub(client, user.id):
        await send_force_sub(message)
        return
    await add_user(user.id, user.first_name, user.username)

    file_id, file_unique_id, file_name, file_size, mime_type = get_file_info(message)
    if not file_id:
        await message.reply_text("❌ Unsupported file type!", quote=True)
        return

    pending_uploads[user.id] = {
        "file_id": file_id, "file_unique_id": file_unique_id,
        "file_name": file_name, "file_size": file_size,
        "mime_type": mime_type, "from_chat_id": message.chat.id,
        "message_id": message.id,
    }

    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔒 Pᴇʀᴍᴀɴᴇɴᴛ", callback_data="linktype_permanent"),
        InlineKeyboardButton("⏰ 24ʜʀ",        callback_data="linktype_24hr"),
    ]])
    await message.reply_text(Script.CHOOSE_LINK_TYPE, reply_markup=buttons, quote=True)


# ─── Process file after link type chosen ──────────────────────────────────────
async def process_file(client: Client, query: CallbackQuery, permanent: bool):
    user = query.from_user
    info = pending_uploads.pop(user.id, None)
    if not info:
        await query.message.edit_text("❌ Session expired. Please re-send your file.")
        return

    await query.message.edit_text("⏳ **Processing your file...**")

    try:
        forwarded = await client.forward_messages(
            chat_id=Config.BIN_CHANNEL,
            from_chat_id=info["from_chat_id"],
            message_ids=info["message_id"])
        msg_id = forwarded.id
    except Exception as e:
        logger.error(f"Forward error: {e}")
        await query.message.edit_text(f"❌ Failed to store file.\n`{e}`")
        return

    file_hash, _ = await save_file(
        info["file_id"], info["file_unique_id"], info["file_name"],
        info["file_size"], info["mime_type"], msg_id, user.id, permanent)

    await query.message.edit_text(
        build_link_message(info["file_name"], humanbytes(info["file_size"]),
                           file_hash, permanent),
        reply_markup=build_file_buttons(file_hash, permanent),
        disable_web_page_preview=True)


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
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("👤 Pʀᴏғɪʟᴇ Lɪɴᴋ", url=profile_url)]])
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


# ─── /stats ───────────────────────────────────────────────────────────────────
async def stats_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ Not authorized!", quote=True)
        return
    users     = await get_user_count()
    files     = await get_file_count()
    permanent = await get_permanent_count()
    temp      = await get_temp_count()
    await message.reply_text(
        Script.STATS_TXT.format(users=users, files=files, permanent=permanent, temp=temp),
        quote=True)


# ─── /broadcast ───────────────────────────────────────────────────────────────
async def broadcast_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        await message.reply_text("❌ Not authorized!", quote=True)
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


# ─── /cleanup ─────────────────────────────────────────────────────────────────
async def cleanup_handler(client: Client, message: Message):
    if message.from_user.id not in Config.ADMINS and message.from_user.id != Config.OWNER_ID:
        return
    deleted = await delete_expired_files()
    await message.reply_text(f"✅ Cleaned up {deleted} expired temp records.", quote=True)


# ─── /help ────────────────────────────────────────────────────────────────────
async def help_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Hᴏᴍᴇ",  callback_data="start"),
         InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about")]
    ])
    await message.reply_text(Script.HELP_TXT, reply_markup=buttons, quote=True)


# ─── /about ───────────────────────────────────────────────────────────────────
async def about_handler(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Hᴏᴍᴇ", callback_data="start"),
         InlineKeyboardButton("📚 Hᴇʟᴘ", callback_data="help")]
    ])
    bot_user = Config.BOT_USERNAME or "FileStreamBot"
    await message.reply_text(
        Script.ABOUT_TXT.format(bot_user, "FileStreamBot"),
        reply_markup=buttons, quote=True, disable_web_page_preview=True)


# ─── Callbacks ────────────────────────────────────────────────────────────────
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user = query.from_user

    # ── Link type ──────────────────────────────────────────
    if data == "linktype_permanent":
        await process_file(client, query, permanent=True)

    elif data == "linktype_24hr":
        await process_file(client, query, permanent=False)

    # ── Files list pagination ──────────────────────────────
    elif data.startswith("filespage_"):
        page = int(data.split("_", 1)[1])
        text, markup = await build_files_page(user.id, page)
        if markup is None:
            await query.message.edit_text(text)
        else:
            try:
                await query.message.edit_text(text, reply_markup=markup)
            except Exception:
                pass

    # ── File detail view ───────────────────────────────────
    elif data.startswith("filedetail_"):
        file_hash = data[len("filedetail_"):]
        text, markup = await build_file_detail(file_hash, user.id)
        if markup:
            try:
                await query.message.edit_text(
                    text, reply_markup=markup, disable_web_page_preview=True)
            except Exception:
                await query.answer("Error showing file details.", show_alert=True)
                return
        else:
            await query.answer(text, show_alert=True)

    # ── Revoke (from /files list — only owner can) ─────────
    elif data.startswith("myrevoke_"):
        file_hash = data[len("myrevoke_"):]
        ok = await delete_file_by_hash(file_hash, uploader_id=user.id)
        if ok:
            # Refresh the list
            text, markup = await build_files_page(user.id, 0)
            try:
                await query.message.edit_text(
                    "✅ File revoked!\n\n" + text,
                    reply_markup=markup)
            except Exception:
                await query.answer("✅ File revoked!", show_alert=True)
        else:
            await query.answer("❌ Could not revoke. Not your file?", show_alert=True)
            return

    # ── Revoke (from link result) ──────────────────────────
    elif data.startswith("revoke_"):
        file_hash = data[7:]
        ok = await delete_file_by_hash(file_hash, uploader_id=user.id)
        if ok:
            await query.message.edit_text("✅ Fɪʟᴇ ʟɪɴᴋ ʜᴀs ʙᴇᴇɴ ʀᴇᴠᴏᴋᴇᴅ!")
        else:
            await query.answer("❌ Failed to revoke. Not your file?", show_alert=True)
            return

    # ── Get File ───────────────────────────────────────────
    elif data.startswith("getfile_"):
        file_hash = data[8:]
        doc = await get_file_by_hash(file_hash)
        if not doc:
            await query.answer("❌ File not found or expired!", show_alert=True)
            return
        if not doc.get("permanent") and time.time() > doc.get("expires_at", 0):
            await query.answer("⏰ This link has expired!", show_alert=True)
            return
        try:
            await client.copy_message(
                chat_id=user.id,
                from_chat_id=Config.BIN_CHANNEL,
                message_id=doc["message_id"])
            await query.answer("✅ File sent to your DM!", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)
            return

    # ── Navigation ─────────────────────────────────────────
    elif data == "check_sub":
        if await check_force_sub(client, user.id):
            await query.message.delete()
            await query.message.reply_text(
                Script.START_TXT.format(user.mention, "👋"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📚 Hᴇʟᴘ",  callback_data="help"),
                     InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about")]
                ]))
        else:
            await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
            return

    elif data == "help":
        await query.message.edit_text(Script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Hᴏᴍᴇ",  callback_data="start"),
                 InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about")]
            ]))

    elif data == "about":
        bot_user = Config.BOT_USERNAME or "FileStreamBot"
        await query.message.edit_text(
            Script.ABOUT_TXT.format(bot_user, "FileStreamBot"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Hᴏᴍᴇ", callback_data="start"),
                 InlineKeyboardButton("📚 Hᴇʟᴘ", callback_data="help")]
            ]), disable_web_page_preview=True)

    elif data == "start":
        await query.message.edit_text(
            Script.START_TXT.format(user.mention, "👋"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Hᴇʟᴘ",  callback_data="help"),
                 InlineKeyboardButton("ℹ️ Aʙᴏᴜᴛ", callback_data="about")],
                [InlineKeyboardButton("👨‍💻 Dᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/Venuboyy")],
            ]))

    elif data == "close":
        await query.message.delete()
        return

    elif data == "noop":
        await query.answer()
        return

    await query.answer()


# ─── Channel/forwarded file handler ───────────────────────────────────────────
async def channel_file_handler(client: Client, message: Message):
    file_id, file_unique_id, file_name, file_size, mime_type = get_file_info(message)
    if not file_id:
        return
    try:
        forwarded = await client.forward_messages(
            chat_id=Config.BIN_CHANNEL,
            from_chat_id=message.chat.id,
            message_ids=message.id)
        msg_id = forwarded.id
    except Exception as e:
        logger.error(f"Channel forward error: {e}")
        return

    file_hash, _ = await save_file(
        file_id, file_unique_id, file_name,
        file_size, mime_type, msg_id, uploader_id=0, permanent=True)

    await message.reply_text(
        build_link_message(file_name, humanbytes(file_size), file_hash, permanent=True),
        reply_markup=build_file_buttons(file_hash, permanent=True),
        quote=True, disable_web_page_preview=True)


# ─── Register all handlers ────────────────────────────────────────────────────
def register_handlers(app: Client):
    from pyrogram.handlers import MessageHandler, CallbackQueryHandler

    _media = (
        filters.document | filters.video | filters.audio |
        filters.photo    | filters.voice | filters.video_note | filters.animation
    )

    app.add_handler(MessageHandler(start_handler,     filters.command("start") & filters.private))
    app.add_handler(MessageHandler(files_handler,     filters.command("files") & filters.private))
    app.add_handler(MessageHandler(help_handler,      filters.command("help")))
    app.add_handler(MessageHandler(about_handler,     filters.command("about")))
    app.add_handler(MessageHandler(info_handler,      filters.command("info")))
    app.add_handler(MessageHandler(stats_handler,     filters.command("stats")))
    app.add_handler(MessageHandler(broadcast_handler, filters.command("broadcast")))
    app.add_handler(MessageHandler(cleanup_handler,   filters.command("cleanup")))

    # Private file uploads
    app.add_handler(MessageHandler(file_handler, filters.private & _media))

    # Forwarded files from channels (auto-permanent)
    app.add_handler(MessageHandler(
        channel_file_handler, filters.forwarded & filters.private & _media))

    app.add_handler(CallbackQueryHandler(callback_handler))
