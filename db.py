import asyncio

db = {
    "queue": asyncio.Queue(),
    "is_playing": False,
    "current_track": None,
    "is_paused": False
}
