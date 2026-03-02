"""
High-performance aiohttp web server for FileStreamBot.
Routes (order matters — specific before wildcard):
  GET /health                          → health check
  GET /stream?hash=<h>                 → raw byte stream (for player)
  GET /watch/<filename>?hash=<h>       → Plyr player page
  GET /<filename>?hash=<h>             → force download
"""
import asyncio
import logging
import time
import urllib.parse
from aiohttp import web
from pyrogram import Client
from pyrogram.errors import FloodWait
from database import get_file_by_hash
from config import Config

logger = logging.getLogger(__name__)

CHUNK_SIZE = 512 * 1024   # 512 KB per chunk read
READ_AHEAD = 6            # chunks to buffer ahead
MAX_CONN   = 10_000


# ─── App + route setup (using Application.router directly to control order) ───
async def handle_index(request: web.Request):
    return web.Response(text="FileStreamBot v2 🚀")

async def handle_health(request: web.Request):
    return web.json_response({"status": "ok", "time": int(time.time())})


# ─── /stream?hash=  (used by Plyr player as video src) ───────────────────────
async def handle_stream(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        return web.Response(status=400, text="Missing ?hash=")
    return await serve_file(request, file_hash, force_download=False)


# ─── /watch/<filename>?hash=  (player HTML page) ─────────────────────────────
async def handle_watch(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        return web.Response(status=400, text="Missing ?hash=")
    file_name = urllib.parse.unquote(request.match_info.get("filename", "video"))
    base      = Config.BASE_URL.rstrip("/")
    html = (PLAYER_HTML
            .replace("__HASH__",      file_hash)
            .replace("__BASE_URL__",  base)
            .replace("__FILE_NAME__", file_name))
    return web.Response(text=html, content_type="text/html")


# ─── /<filename>?hash=  (direct download) ────────────────────────────────────
async def handle_download(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        return web.Response(status=400, text="Missing ?hash=")
    return await serve_file(request, file_hash, force_download=True)


# ─── Core streaming engine ────────────────────────────────────────────────────
async def serve_file(request: web.Request, file_hash: str, force_download: bool):
    # ── DB lookup ──────────────────────────────────────────
    file_doc = await get_file_by_hash(file_hash)
    if not file_doc:
        return web.Response(status=404, text="❌ File not found or link has expired.")
    if not file_doc.get("permanent") and time.time() > file_doc.get("expires_at", 0):
        return web.Response(status=410, text="⏰ This link has expired.")

    bot:       Client = request.app["bot"]
    file_size: int    = file_doc.get("file_size", 0)
    file_name: str    = file_doc.get("file_name", "file")
    mime_type: str    = file_doc.get("mime_type", "application/octet-stream")
    message_id: int   = file_doc["message_id"]

    # ── Range request parsing ──────────────────────────────
    range_header = request.headers.get("Range", "")
    offset = 0
    end    = file_size - 1 if file_size > 0 else 0

    if range_header and file_size > 0:
        try:
            rng    = range_header.replace("bytes=", "").split("-")
            offset = int(rng[0]) if rng[0] else 0
            end    = int(rng[1]) if len(rng) > 1 and rng[1] else file_size - 1
        except Exception:
            pass

    length = max(0, end - offset + 1) if file_size > 0 else 0

    # ── Response headers ───────────────────────────────────
    disposition = (
        f'attachment; filename="{file_name}"' if force_download
        else f'inline; filename="{file_name}"'
    )
    headers = {
        "Content-Type":              mime_type,
        "Content-Disposition":       disposition,
        "Accept-Ranges":             "bytes",
        "Cache-Control":             "no-cache",
        "Access-Control-Allow-Origin": "*",
    }
    if file_size > 0:
        headers["Content-Length"] = str(length)
    if range_header and file_size > 0:
        headers["Content-Range"] = f"bytes {offset}-{end}/{file_size}"
        status = 206
    else:
        status = 200

    response = web.StreamResponse(status=status, headers=headers)

    try:
        await response.prepare(request)
    except Exception as e:
        logger.warning(f"prepare error: {e}")
        return response

    # ── Stream from Telegram ───────────────────────────────
    try:
        tg_msg = await bot.get_messages(Config.BIN_CHANNEL, message_id)
        if not tg_msg or tg_msg.empty:
            await response.write(b"")
            await response.write_eof()
            return response

        # Producer fills queue, consumer writes to response
        queue: asyncio.Queue = asyncio.Queue(maxsize=READ_AHEAD)

        async def producer():
            try:
                async for chunk in bot.stream_media(tg_msg, offset=offset):
                    await queue.put(chunk)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.error(f"Telegram stream error: {e}")
            finally:
                await queue.put(None)  # sentinel

        prod_task = asyncio.create_task(producer())
        bytes_sent = 0

        while True:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Stream timeout waiting for chunk")
                break

            if chunk is None:
                break

            # Respect content-length: only send what was requested
            if length > 0 and bytes_sent + len(chunk) > length:
                chunk = chunk[:length - bytes_sent]

            try:
                await response.write(chunk)
            except (ConnectionResetError, ConnectionAbortedError):
                break  # client disconnected
            except Exception:
                break

            bytes_sent += len(chunk)
            if length > 0 and bytes_sent >= length:
                break

        prod_task.cancel()
        try:
            await prod_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        logger.error(f"serve_file error hash={file_hash}: {e}")

    try:
        await response.write_eof()
    except Exception:
        pass

    return response


# ─── Plyr player HTML ─────────────────────────────────────────────────────────
PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>__FILE_NAME__</title>
<link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d0d;min-height:100vh;display:flex;flex-direction:column;
     align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:#fff}
.wrap{width:100%;max-width:980px;padding:16px}
h1{text-align:center;margin-bottom:14px;font-size:1.1rem;word-break:break-all;
   background:linear-gradient(135deg,#4CAF50,#2196F3);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.player-box{border-radius:12px;overflow:hidden;box-shadow:0 6px 32px rgba(0,0,0,.7)}
.actions{display:flex;gap:10px;margin-top:14px;justify-content:center;flex-wrap:wrap}
.btn{padding:10px 24px;border-radius:8px;font-weight:600;font-size:.9rem;
     text-decoration:none;color:#fff;border:none;cursor:pointer;transition:opacity .2s}
.btn:hover{opacity:.82}
.dl{background:linear-gradient(135deg,#4CAF50,#2196F3)}
.cp{background:#333}
.info{margin-top:10px;text-align:center;color:#555;font-size:.78rem}
#toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);
       background:#4CAF50;color:#fff;padding:9px 22px;border-radius:8px;
       font-size:.88rem;display:none;z-index:999;pointer-events:none}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎬 __FILE_NAME__</h1>
  <div class="player-box">
    <video id="player" playsinline controls crossorigin>
      <source src="__BASE_URL__/stream?hash=__HASH__">
    </video>
  </div>
  <div class="actions">
    <a class="btn dl" href="__BASE_URL__/__FILE_NAME__?hash=__HASH__" download>⬇️ Download</a>
    <button class="btn cp" onclick="copy()">📋 Copy Link</button>
  </div>
  <div class="info">⚡ FileStreamBot · Dev: @Venuboyy</div>
</div>
<div id="toast">✅ Copied!</div>
<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
<script>
new Plyr('#player',{
  controls:['play-large','rewind','play','fast-forward','progress',
            'current-time','duration','mute','volume','settings','fullscreen'],
  settings:['speed'],speed:{selected:1,options:[0.5,0.75,1,1.25,1.5,2]},
  keyboard:{focused:true,global:true}
});
function copy(){
  navigator.clipboard.writeText(window.location.href).then(()=>{
    const t=document.getElementById('toast');
    t.style.display='block';
    setTimeout(()=>{t.style.display='none'},2200);
  });
}
</script>
</body>
</html>"""


# ─── App factory ──────────────────────────────────────────────────────────────
def create_app(bot_client: Client) -> web.Application:
    app = web.Application(client_max_size=4 * 1024 ** 3)
    app["bot"] = bot_client

    # ORDER MATTERS: specific routes before wildcard /{filename}
    app.router.add_get("/",                  handle_index)
    app.router.add_get("/health",            handle_health)
    app.router.add_get("/stream",            handle_stream)       # /stream?hash=
    app.router.add_get("/watch/",            handle_watch)        # /watch/?hash=
    app.router.add_get("/watch/{filename}",  handle_watch)        # /watch/name?hash=
    app.router.add_get("/{filename}",        handle_download)     # /name.mkv?hash=

    return app


async def start_web_server(bot_client: Client):
    app    = create_app(bot_client)
    runner = web.AppRunner(app, access_log=None, handler_cancellation=True)
    await runner.setup()
    site = web.TCPSite(
        runner, Config.HOST, Config.PORT,
        backlog=1024, reuse_address=True, reuse_port=True,
    )
    await site.start()
    logger.info(f"⚡ Web server → http://{Config.HOST}:{Config.PORT}")
    return runner
