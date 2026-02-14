import asyncio
import logging
import os
import sys

import yt_dlp
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

# --- REFINED LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger("VCBot")
LOGGER.setLevel(logging.DEBUG)

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = int(os.getenv("CHAT_ID", 0))

app = Client(
    "tgvc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


async def get_audio_info(query):
    """Retrieves metadata using yt-dlp flat extraction."""
    LOGGER.info("Starting search for: %s", query)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "extract_flat": True,
        "noplaylist": True,
    }

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            LOGGER.debug("Extracting info from YouTube...")
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if not info or "entries" not in info or not info["entries"]:
                LOGGER.warning("No entries found for query: %s", query)
                return None

            video = info["entries"][0]
            data = {
                "title": video.get("title", "Unknown"),
                "url": f"https://www.youtube.com/watch?v={video['id']}",
                "duration": int(video.get("duration", 0)) or 300,
            }
            LOGGER.info("Found: %s", data["title"])
            return data

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, extract)


async def resolve_direct_url(video_url):
    """Resolves direct media link."""
    LOGGER.info("Resolving direct stream URL...")
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "source_address": "0.0.0.0",
    }

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            url = info.get("url")
            LOGGER.debug("Stream URL successfully resolved.")
            return url

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, extract)
