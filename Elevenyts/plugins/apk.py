from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

AFK = {}

@Client.on_message(filters.command("afk"))
async def set_afk(client, message: Message):
    reason = " ".join(message.command[1:]) or "AFK"
    AFK[message.from_user.id] = {
        "reason": reason,
        "time": datetime.now()
    }
    await message.reply_text(
        f"😴 AFK Enabled\n\nReason: {reason}"
    )

@Client.on_message(filters.reply & filters.text)
async def afk_reply(client, message: Message):
    replied = message.reply_to_message.from_user
    if not replied:
        return

    if replied.id in AFK:
        afk = AFK[replied.id]
        duration = datetime.now() - afk["time"]

        await message.reply_text(
            f"😴 User is AFK\n"
            f"📝 Reason: {afk['reason']}\n"
            f"⏰ Since: {str(duration).split('.')[0]}"
        )

@Client.on_message(filters.text & ~filters.command("afk"))
async def afk_back(client, message: Message):
    if not message.from_user:
        return

    if message.from_user.id in AFK:
        afk = AFK.pop(message.from_user.id)
        duration = datetime.now() - afk["time"]

        await message.reply_text(
            f"✅ Welcome back!\n"
            f"AFK duration: {str(duration).split('.')[0]}"
        )
