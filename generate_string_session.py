import asyncio

# 1. Create the loop manually before importing Pyrogram
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# 2. Now import Pyrogram
from pyrogram import Client as c


async def main():
    API_ID = input("\nEnter Your API_ID:\n > ")
    API_HASH = input("\nEnter Your API_HASH:\n > ")

    print("\n\n Enter Phone number when asked.\n\n")

    async with c(":memory:", api_id=int(API_ID), api_hash=API_HASH) as i:
        ss = await i.export_session_string()
        print("\nHERE IS YOUR STRING SESSION, COPY IT, DON'T SHARE!!\n")
        print(f"\n{ss}\n")

if __name__ == "__main__":
    asyncio.run(main())
