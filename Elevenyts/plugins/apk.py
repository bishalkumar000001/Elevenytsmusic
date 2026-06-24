# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pyrogram import filters, types
from datetime import datetime
import time
import asyncio

# -------------------------------------------------
# USE YOUR EXISTING DB FROM MAIN BOT
# -------------------------------------------------
from Elevenyts import app, db

afk_col = db["afk"]
LAST_SEEN = {}
AFK_COOLDOWN = {}

# -------------------------------------------------
# FORMAT TIME
# -------------------------------------------------
def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds//60)}m"
    elif seconds < 86400:
        return f"{int(seconds//3600)}h"
    else:
        return f"{int(seconds//86400)}d"

# -------------------------------------------------
# TRACK USER ACTIVITY
# -------------------------------------------------
@app.on_message(filters.text & ~filters.bot)
async def track_activity(client, message: types.Message):
    if not message.from_user:
        return
    LAST_SEEN[message.from_user.id] = time.time()

# -------------------------------------------------
# SET AFK COMMAND
# -------------------------------------------------
@app.on_message(filters.command("afk") & ~app.bl_users)
async def set_afk(client, message: types.Message):
    if not message.from_user:
        return

    user = message.from_user
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason"

    await afk_col.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "user_id": user.id,
                "name": user.first_name,
                "reason": reason,
                "time": time.time()
            }
        },
        upsert=True
    )

    await message.reply_text(
        "😴 **AFK Activated**\n"
        f"📝 Reason: `{reason}`\n\n"
        "⚡ I will notify others when you are mentioned."
    )

# -------------------------------------------------
# AUTO REMOVE AFK (WHEN USER RETURNS)
# -------------------------------------------------
@app.on_message(filters.text & ~filters.bot & ~filters.command("afk"))
async def remove_afk(client, message: types.Message):
    if not message.from_user:
        return

    user_id = message.from_user.id

    afk = await afk_col.find_one({"user_id": user_id})

    if afk:
        duration = time.time() - afk["time"]

        await afk_col.delete_one({"user_id": user_id})

        # anti spam cooldown
        if user_id in AFK_COOLDOWN:
            if time.time() - AFK_COOLDOWN[user_id] < 5:
                return

        AFK_COOLDOWN[user_id] = time.time()

        await message.reply_text(
            "👋 **Welcome Back!**\n"
            f"⏳ AFK Duration: `{format_time(duration)}`"
        )

# -------------------------------------------------
# AFK MENTION HANDLER (SMART)
# -------------------------------------------------
@app.on_message(filters.mentioned & ~filters.bot)
async def afk_mention(client, message: types.Message):
    if not message.entities:
        return

    for entity in message.entities:
        if entity.user:
            uid = entity.user.id

            afk = await afk_col.find_one({"user_id": uid})

            if afk:
                duration = time.time() - afk["time"]

                text = (
                    "⚠️ **USER IS AFK**\n"
                    f"👤 Name: `{afk['name']}`\n"
                    f"📝 Reason: `{afk['reason']}`\n"
                    f"⏳ Since: `{format_time(duration)}` ago"
                )

                await message.reply_text(text)

                # optional DM notification
                try:
                    await client.send_message(
                        uid,
                        "📩 You were mentioned!\n\n" + text
                    )
                except:
                    pass

# -------------------------------------------------
# AUTO AFK (INACTIVITY SYSTEM - 30 MIN)
# -------------------------------------------------
async def auto_afk_checker(client):
    while True:
        now = time.time()

        for user_id, last in list(LAST_SEEN.items()):
            if now - last > 1800:  # 30 minutes
                if not await afk_col.find_one({"user_id": user_id}):
                    await afk_col.insert_one({
                        "user_id": user_id,
                        "name": "User",
                        "reason": "Auto AFK (Inactive)",
                        "time": now
                    })

        await asyncio.sleep(60)

# -------------------------------------------------
# START AFK SYSTEM
# -------------------------------------------------
def start_afk(client):
    client.loop.create_task(auto_afk_checker(client))
