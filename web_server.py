"""
Aiohttp web server — supports new URL format:
  GET /<filename>?hash=<hash>          → download
  GET /watch/<filename>?hash=<hash>    → player page
  GET /stream?hash=<hash>              → raw stream (used by player)
"""
import asyncio
import logging
import time
import urllib.parse
from aiohttp import web
from pyrogram import Client
from database import get_file_by_hash
from config import Config

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


# ─── Health ───────────────────────────────────────────────────────────────────
@routes.get("/")
async def index(request):
    return web.Response(text="FileStreamBot v2 🚀")

@routes.get("/health")
async def health(request):
    return web.json_response({"status": "ok", "time": int(time.time())})


# ─── Download  /<filename>?hash=<hash> ───────────────────────────────────────
@routes.get("/{filename}")
async def download(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        raise web.HTTPBadRequest(text="Missing ?hash= parameter")
    return await serve_file(request, file_hash, download=True)


# ─── Watch  /watch/<filename>?hash=<hash> ────────────────────────────────────
@routes.get("/watch/{filename}")
async def watch(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        raise web.HTTPBadRequest(text="Missing ?hash= parameter")
    file_name = urllib.parse.unquote(request.match_info["filename"])
    html = PLAYER_HTML \
        .replace("__HASH__", file_hash) \
        .replace("__BASE_URL__", Config.BASE_URL.rstrip("/")) \
        .replace("__FILE_NAME__", file_name)
    return web.Response(text=html, content_type="text/html")


# ─── Raw stream  /stream?hash=<hash> ─────────────────────────────────────────
@routes.get("/stream")
async def stream(request: web.Request):
    file_hash = request.rel_url.query.get("hash", "")
    if not file_hash:
        raise web.HTTPBadRequest(text="Missing ?hash= parameter")
    return await serve_file(request, file_hash, download=False)


# ─── Core serve ───────────────────────────────────────────────────────────────
async def serve_file(request: web.Request, file_hash: str, download: bool):
    file_doc = await get_file_by_hash(file_hash)
    if not file_doc:
        raise web.HTTPNotFound(text="File not found or link has expired.")

    # Check expiry for temp links
    if not file_doc.get("permanent") and time.time() > file_doc.get("expires_at", 0):
        raise web.HTTPGone(text="This link has expired.")

    client: Client = request.app["bot"]
    file_size  = file_doc["file_size"]
    file_name  = file_doc["file_name"]
    mime_type  = file_doc.get("mime_type", "application/octet-stream")
    message_id = file_doc["message_id"]

    # Range request support (needed for video seeking)
    range_header = request.headers.get("Range")
    offset, end  = 0, file_size - 1

    if range_header:
        rng = range_header.strip().replace("bytes=", "").split("-")
        try:
            offset = int(rng[0]) if rng[0] else 0
            end    = int(rng[1]) if len(rng) > 1 and rng[1] else file_size - 1
        except Exception:
            pass

    length = end - offset + 1

    disposition = (
        f'attachment; filename="{file_name}"' if download
        else f'inline; filename="{file_name}"'
    )

    headers = {
        "Content-Type": mime_type,
        "Content-Disposition": disposition,
        "Content-Length": str(length),
        "Accept-Ranges": "bytes",
    }

    if range_header:
        headers["Content-Range"] = f"bytes {offset}-{end}/{file_size}"
        status = 206
    else:
        status = 200

    response = web.StreamResponse(status=status, headers=headers)
    await response.prepare(request)

    try:
        tg_message = await client.get_messages(Config.BIN_CHANNEL, message_id)
        async for chunk in client.stream_media(tg_message, offset=offset, limit=length):
            if chunk:
                await response.write(chunk)
                if response.force_close:
                    break
    except Exception as e:
        logger.error(f"Stream error: {e}")

    await response.write_eof()
    return response


# ─── Plyr Player ──────────────────────────────────────────────────────────────
PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>__FILE_NAME__ — FileStreamBot</title>
<link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d0d;display:flex;flex-direction:column;align-items:center;
     justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;color:#fff}
.wrap{width:100%;max-width:980px;padding:20px}
h1{text-align:center;margin-bottom:18px;font-size:1.5rem;
   background:linear-gradient(135deg,#4CAF50,#2196F3);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.player-box{border-radius:14px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.6)}
.plyr{border-radius:14px}
.actions{display:flex;gap:12px;margin-top:18px;justify-content:center}
.btn{padding:11px 28px;border-radius:8px;font-weight:600;font-size:.95rem;
     text-decoration:none;color:#fff;transition:opacity .2s}
.btn-dl{background:linear-gradient(135deg,#4CAF50,#2196F3)}
.btn-dl:hover,.btn-share:hover{opacity:.88}
.btn-share{background:#2196F3}
.info{margin-top:14px;text-align:center;color:#666;font-size:.82rem}
.brand{margin-top:20px;text-align:center;color:#444;font-size:.78rem}
.brand a{color:#4CAF50;text-decoration:none}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎬 __FILE_NAME__</h1>
  <div class="player-box">
    <video id="player" playsinline controls>
      <source src="__BASE_URL__/stream?hash=__HASH__" type="video/mp4">
    </video>
  </div>
  <div class="actions">
    <a class="btn btn-dl" href="__BASE_URL__/__FILE_NAME__?hash=__HASH__">⬇️ Download</a>
  </div>
  <div class="info">⚠️ Link may expire — save the file now</div>
  <div class="brand">Powered by <a href="https://t.me/Venuboyy">FileStreamBot</a> · Dev: <a href="https://t.me/Venuboyy">@Venuboyy</a></div>
</div>
<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
<script>
new Plyr('#player',{
  controls:['play-large','rewind','play','fast-forward','progress',
            'current-time','duration','mute','volume','captions',
            'settings','pip','airplay','fullscreen'],
  settings:['captions','quality','speed'],
  speed:{selected:1,options:[0.5,0.75,1,1.25,1.5,2]},
  keyboard:{focused:true,global:true}
});
</script>
</body>
</html>"""


# ─── App factory ──────────────────────────────────────────────────────────────
def create_app(bot_client: Client) -> web.Application:
    app = web.Application()
    app["bot"] = bot_client
    app.add_routes(routes)
    return app

async def start_web_server(bot_client: Client):
    app = create_app(bot_client)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, Config.HOST, Config.PORT)
    await site.start()
    logger.info(f"Web server on {Config.HOST}:{Config.PORT}")
    return runner
