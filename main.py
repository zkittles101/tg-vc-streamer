import asyncio
import ntgcalls
import socket
import time
from os import getenv
from pyrogram import filters, idle, utils, Client
from pytgcalls import PyTgCalls
from flask import Flask
from threading import Thread

# Import from your local modules
from functions import get_audio_info, resolve_direct_url, CHAT_ID, LOGGER
import db

# --- 1. DUMMY HEALTH CHECK (For Koyeb/Render/Railway) ---
health_app = Flask(__name__)
@health_app.route('/')
def health(): return "Bot is running"


def run_health():
    # Listens on port 8080 (standard for cloud services)
    health_app.run(host="0.0.0.0", port=8080)


# --- 2. CONFIGURATION ---
API_ID = getenv("API_ID")
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")
SESSION_STRING = getenv("SESSION_STRING")

# --- 3. PROXY & NETWORK UTILS ---


def wait_for_proxy(host, port, timeout=15):
    """Wait for wireproxy to open its local port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                LOGGER.info(f" Wireproxy detected on {host}:{port}")
                return True
        except:
            LOGGER.warning(f" Waiting for Wireproxy on {host}:{port}...")
            time.sleep(2)
    return False


warp_proxy = {
    "scheme": "socks5",
    "hostname": "127.0.0.1",
    "port": 40000
}

# --- 4. HELPERS & WORKERS ---


def format_time(seconds):
    """Formats seconds into MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


async def play_worker():
    """Worker handling the music queue with zero overhead."""
    while True:
        track = await db.db["queue"].get()
        db.db["current_track"] = track
        db.db["is_playing"] = True

        LOGGER.info("Worker: Processing '%s'", track['title'])

        try:
            # Resolve the heavy streaming URL
            direct_link = await resolve_direct_url(track["url"])

            # Start Playback in Voice Chat
            await call_py.play(CHAT_ID, direct_link)
            LOGGER.info("Worker: Playback started.")

            # Send static notification
            status_text = (
                "🎵 **Now Playing**\n\n"
                f"📝 **Title:** `{track['title']}`\n"
                f"👤 **Requester:** {track['requester']}\n"
                f"🕒 **Duration:** `{format_time(track['duration'])}`"
            )
            await app.send_message(CHAT_ID, status_text)

            # Wait for track duration while checking for skip signals
            sleep_time = track["duration"] + 2
            for _ in range(sleep_time):
                if not db.db["is_playing"]:
                    break
                await asyncio.sleep(1)

        except ntgcalls.TelegramServerError:
            LOGGER.error(
                "Worker: Telegram VoIP Server rejected the connection (IP Block).")
            await app.send_message(CHAT_ID, " **Voice Server Error:** Check proxy status/logs.")
        except Exception as err:
            LOGGER.error("Worker Error: %s", err, exc_info=True)
        finally:
            db.db["is_playing"] = False
            try:
                await call_py.leave_call(CHAT_ID)
                LOGGER.info("Worker: Left VC.")
            except:
                pass

            db.db["current_track"] = None
            db.db["queue"].task_done()
            LOGGER.info("Worker: Ready for next item.")

# --- 5. INITIALIZE CLIENTS ---
app = Client(
    "tg_vc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=SESSION_STRING,
    proxy=warp_proxy,
    in_memory=True
)

# Peer ID Monkeypatch


def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    return "chat"


utils.get_peer_type = get_peer_type_new
call_py = PyTgCalls(app)

# --- 6. COMMAND HANDLERS ---


@app.on_message(filters.command("play") & filters.chat(CHAT_ID))
async def play_cmd(_, message):
    text_parts = message.text.split(None, 1)
    query = text_parts[1] if len(text_parts) > 1 else None
    if not query:
        return await message.reply_text("❌ Usage: `/play [song name]`")
    search_msg = await message.reply_text("🔍 Searching...")
    info = await get_audio_info(query)
    if not info:
        return await search_msg.edit("❌ No results found.")
    info["requester"] = message.from_user.mention
    await db.db["queue"].put(info)
    if db.db["is_playing"]:
        await search_msg.edit(f"📝 **Queued:** `{info['title']}`")
    else:
        await search_msg.delete()


@app.on_message(filters.command("skip") & filters.chat(CHAT_ID))
async def skip_cmd(_, message):
    if not db.db["is_playing"]:
        return await message.reply_text("❌ Nothing is playing.")
    db.db["is_playing"] = False
    await message.reply_text("⏭ **Skipped.**")


@app.on_message(filters.command("stop") & filters.chat(CHAT_ID))
async def stop_cmd(_, message):
    while not db.db["queue"].empty():
        try:
            db.db["queue"].get_nowait()
            db.db["queue"].task_done()
        except asyncio.QueueEmpty:
            break
    db.db["is_playing"] = False
    await message.reply_text("⏹ **Stopped and Cleared.**")


@app.on_message(filters.command("queue") & filters.chat(CHAT_ID))
async def queue_cmd(_, message):
    curr = db.db.get("current_track")
    if not curr and db.db["queue"].empty():
        return await message.reply_text("📋 Queue is empty.")
    t_title = curr["title"] if curr else "None"
    q_size = db.db["queue"].qsize()
    await message.reply_text(f"▶️ **Now:** `{t_title}`\n📋 **Queue:** `{q_size}`")


@app.on_message(filters.command("help") & filters.chat(CHAT_ID))
async def help_cmd(_, message):
    help_text = (
        "🛠 **VC Bot Commands**\n\n"
        "🔹 `/play [song]` - Play from YouTube\n"
        "🔹 `/skip` - Next track\n"
        "🔹 `/stop` - Stop and clear queue\n"
        "🔹 `/queue` - Show current status\n"
        "🔹 `/help` - Show this menu"
    )
    await message.reply_text(help_text)

# --- 7. MAIN RUNNER ---


async def main():
    # Start Health Check Server in background
    Thread(target=run_health, daemon=True).start()

    # Wait for Proxy bridge
    if not wait_for_proxy("127.0.0.1", 40000):
        LOGGER.error(
            "❌ Wireproxy failed to start. Continuing without proxy check...")

    LOGGER.info("Starting Client and PyTgCalls...")
    await app.start()
    await call_py.start()

    # Start the music worker (now correctly defined above)
    asyncio.create_task(play_worker())

    LOGGER.info("--- VC Bot Online ---")
    await idle()

if __name__ == "__main__":
    app.run(main())
