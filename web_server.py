"""
Aiohttp web server for streaming and downloading files via Telegram Bot API.
Supports files up to 4GB via range requests.
"""
import asyncio
import logging
import time
from aiohttp import web
from pyrogram import Client
from database import get_file
from config import Config

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

# ─── Health check ─────────────────────────────────────────────────────────────
@routes.get("/")
async def index(request: web.Request):
    return web.Response(text="FileStreamBot is running! 🚀")

@routes.get("/health")
async def health(request: web.Request):
    return web.json_response({"status": "ok", "time": int(time.time())})

# ─── Download ─────────────────────────────────────────────────────────────────
@routes.get("/dl/{file_id}")
async def download(request: web.Request):
    file_db_id = request.match_info["file_id"]
    return await serve_file(request, file_db_id, download=True)

# ─── Stream / Watch ───────────────────────────────────────────────────────────
@routes.get("/watch/{file_id}")
async def watch(request: web.Request):
    file_db_id = request.match_info["file_id"]
    # Serve the player HTML page
    html = PLAYER_HTML.replace("__FILE_ID__", file_db_id).replace("__BASE_URL__", Config.BASE_URL)
    return web.Response(text=html, content_type="text/html")

@routes.get("/stream/{file_id}")
async def stream(request: web.Request):
    file_db_id = request.match_info["file_id"]
    return await serve_file(request, file_db_id, download=False)

# ─── Core serve function ──────────────────────────────────────────────────────
async def serve_file(request: web.Request, file_db_id: str, download: bool = False):
    file_doc = await get_file(file_db_id)
    if not file_doc:
        raise web.HTTPNotFound(text="File not found or link has expired.")

    if time.time() > file_doc.get("expires_at", 0):
        raise web.HTTPGone(text="This link has expired.")

    client: Client = request.app["bot"]
    file_size = file_doc["file_size"]
    file_name = file_doc["file_name"]
    mime_type = file_doc.get("mime_type", "application/octet-stream")
    message_id = file_doc["message_id"]

    # Range request support
    range_header = request.headers.get("Range")
    offset = 0
    end = file_size - 1

    if range_header:
        range_val = range_header.strip().replace("bytes=", "")
        parts = range_val.split("-")
        try:
            offset = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
        except Exception:
            pass

    length = end - offset + 1

    if download:
        disposition = f'attachment; filename="{file_name}"'
    else:
        disposition = f'inline; filename="{file_name}"'

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

    # Stream from Telegram
    try:
        async for chunk in client.stream_media(
            (await client.get_messages(Config.BIN_CHANNEL, message_id)),
            offset=offset,
            limit=length
        ):
            if chunk:
                await response.write(chunk)
                if response.force_close:
                    break
    except Exception as e:
        logger.error(f"Stream error: {e}")

    await response.write_eof()
    return response

# ─── Plyr Player HTML ─────────────────────────────────────────────────────────
PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FileStreamBot Player</title>
<link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #0f0f0f;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Segoe UI', sans-serif;
    color: #fff;
  }
  .wrapper {
    width: 100%;
    max-width: 960px;
    padding: 20px;
  }
  .header {
    text-align: center;
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 1.6rem;
    background: linear-gradient(135deg, #4CAF50, #2196F3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .player-container {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }
  .plyr { border-radius: 12px; }
  .download-btn {
    display: block;
    margin: 20px auto 0;
    padding: 12px 32px;
    background: linear-gradient(135deg, #4CAF50, #2196F3);
    color: white;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 1rem;
    text-align: center;
    max-width: 300px;
    transition: opacity 0.2s;
  }
  .download-btn:hover { opacity: 0.9; }
  .info-box {
    margin-top: 16px;
    padding: 12px 16px;
    background: #1a1a1a;
    border-radius: 8px;
    font-size: 0.9rem;
    color: #aaa;
    text-align: center;
  }
  .brand {
    margin-top: 24px;
    text-align: center;
    color: #555;
    font-size: 0.8rem;
  }
  .brand a { color: #4CAF50; text-decoration: none; }
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🎬 FileStreamBot Player</h1>
  </div>
  <div class="player-container">
    <video id="player" playsinline controls>
      <source src="__BASE_URL__/stream/__FILE_ID__" type="video/mp4">
    </video>
  </div>
  <a class="download-btn" href="__BASE_URL__/dl/__FILE_ID__">⬇️ Download File</a>
  <div class="info-box">⚠️ Link expires in 24 hours</div>
  <div class="brand">Powered by <a href="https://t.me/Venuboyy">FileStreamBot</a> | Dev: <a href="https://t.me/Venuboyy">@Venuboyy</a></div>
</div>
<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
<script>
  const player = new Plyr('#player', {
    controls: [
      'play-large','rewind','play','fast-forward','progress',
      'current-time','duration','mute','volume','captions',
      'settings','pip','airplay','fullscreen'
    ],
    settings: ['captions','quality','speed'],
    speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
    keyboard: { focused: true, global: true }
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
    logger.info(f"Web server started on {Config.HOST}:{Config.PORT}")
    return runner
