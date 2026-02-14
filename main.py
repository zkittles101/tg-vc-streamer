import asyncio
from pyrogram import filters, idle, utils
from pytgcalls import PyTgCalls

from functions import app, get_audio_info, resolve_direct_url, CHAT_ID, LOGGER
import db

# --- PEER ID MONKEYPATCH ---


def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    return "chat"


utils.get_peer_type = get_peer_type_new
# ---------------------------

call_py = PyTgCalls(app)


def format_time(seconds):
    """Formats seconds into MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


async def play_worker():
    """Simplified worker: Zero overhead, no live updates."""
    while True:
        track = await db.db["queue"].get()
        db.db["current_track"] = track
        db.db["is_playing"] = True

        LOGGER.info("Worker: Processing '%s'", track['title'])

        try:
            # Resolve the heavy link
            direct_link = await resolve_direct_url(track["url"])

            # Start Playback
            await call_py.play(CHAT_ID, direct_link)
            LOGGER.info("Worker: Playback started.")

            # Send a single, static notification
            status_text = (
                "🎵 **Now Playing**\n\n"
                f"📝 **Title:** `{track['title']}`\n"
                f"👤 **Requester:** {track['requester']}\n"
                f"🕒 **Duration:** `{format_time(track['duration'])}`"
            )
            await app.send_message(CHAT_ID, status_text)

            # Instead of a loop, we just sleep for the duration of the track
            # This is the most performance-efficient way to handle playback
            sleep_time = track["duration"] + 2

            # We use a small loop only to check if the user triggered /skip
            for _ in range(sleep_time):
                if not db.db["is_playing"]:
                    break
                await asyncio.sleep(1)

        except Exception as err:
            LOGGER.error("Worker Error: %s", err, exc_info=True)
        finally:
            db.db["is_playing"] = False
            try:
                await call_py.leave_call(CHAT_ID)
                LOGGER.info("Worker: Playback ended/skipped. Left VC.")
            except:
                pass

            db.db["current_track"] = None
            db.db["queue"].task_done()
            LOGGER.info("Worker: Ready for next queue item.")


@app.on_message(filters.command("play") & filters.chat(CHAT_ID))
async def play_cmd(_, message):
    LOGGER.info("Command: /play received")
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


async def main():
    LOGGER.info("Initializing...")
    await app.start()
    await call_py.start()
    asyncio.create_task(play_worker())
    LOGGER.info("--- VC Bot Online ---")
    await idle()


if __name__ == "__main__":
    app.run(main())
