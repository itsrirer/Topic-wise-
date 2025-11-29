from pyrogram import Client, filters
from pyrogram.types import Message
import os, json, asyncio

# Required env vars
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not (API_ID and API_HASH and BOT_TOKEN and OWNER_ID):
    raise SystemExit("Missing one of required env vars: API_ID, API_HASH, BOT_TOKEN, OWNER_ID")

DATA_FILE = "db.json"

def load_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"sources": [], "dest": None, "forward_on": False}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

app = Client("topic_forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_field(text, field):
    if not text:
        return None
    for line in text.splitlines():
        if line.lower().startswith(field.lower()):
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    return None

async def get_or_create_topic(chat_id: int, topic_name: str):
    # Try to find existing topics (Pyrogram method: get_forum_topics)
    try:
        topics = await app.get_forum_topics(chat_id)
        for t in topics:
            # t.name or t.title depending on version
            name = getattr(t, "name", None) or getattr(t, "title", None)
            tid = getattr(t, "id", None) or getattr(t, "message_thread_id", None)
            if name and tid and name.lower() == topic_name.lower():
                return tid
    except Exception:
        # ignore errors and try to create topic
        pass
    # Create a new forum topic
    created = await app.create_forum_topic(chat_id, topic_name)
    return getattr(created, "id", None) or getattr(created, "message_thread_id", None)

# ----------------- Owner-only commands -----------------

@app.on_message(filters.command("addsource") & filters.user(OWNER_ID))
async def cmd_addsource(_, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /addsource -1001234567890")
    try:
        source = int(msg.command[1])
    except:
        return await msg.reply("Invalid source id.")
    db = load_db()
    if source not in db["sources"]:
        db["sources"].append(source)
        save_db(db)
    await msg.reply(f"✅ Source added: `{source}`")

@app.on_message(filters.command("removesource") & filters.user(OWNER_ID))
async def cmd_removesource(_, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /removesource -1001234567890")
    try:
        source = int(msg.command[1])
    except:
        return await msg.reply("Invalid source id.")
    db = load_db()
    if source in db["sources"]:
        db["sources"].remove(source)
        save_db(db)
        await msg.reply(f"✅ Source removed: `{source}`")
    else:
        await msg.reply("Source not found.")

@app.on_message(filters.command("adddest") & filters.user(OWNER_ID))
async def cmd_adddest(_, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply("Usage: /adddest -1001234567890")
    try:
        dest = int(msg.command[1])
    except:
        return await msg.reply("Invalid dest id.")
    db = load_db()
    db["dest"] = dest
    save_db(db)
    await msg.reply(f"✅ Destination set: `{dest}`")

@app.on_message(filters.command("startforward") & filters.user(OWNER_ID))
async def cmd_start(_, msg: Message):
    db = load_db()
    db["forward_on"] = True
    save_db(db)
    await msg.reply("🚀 Auto-forward ENABLED")

@app.on_message(filters.command("stopforward") & filters.user(OWNER_ID))
async def cmd_stop(_, msg: Message):
    db = load_db()
    db["forward_on"] = False
    save_db(db)
    await msg.reply("⛔ Auto-forward DISABLED")

@app.on_message(filters.command("status") & filters.user(OWNER_ID))
async def cmd_status(_, msg: Message):
    db = load_db()
    text = f"📌 BOT STATUS\\nSources: {db['sources']}\\nDestination: {db['dest']}\\nForwarding: {db['forward_on']}"
    await msg.reply(text)

@app.on_message(filters.command("scanold") & filters.user(OWNER_ID))
async def cmd_scanold(_, msg: Message):
    db = load_db()
    if not db["sources"]:
        return await msg.reply("❌ No sources set. Use /addsource")
    if not db["dest"]:
        return await msg.reply("❌ No destination set. Use /adddest")
    await msg.reply("🔍 Starting old messages scan. This may take a while...")
    dest = db["dest"]
    count = 0
    for source in db["sources"]:
        try:
            async for m in app.get_chat_history(source):
                if m.video or m.document:
                    caption = m.caption or ""
                    topic_name = extract_field(caption, "Topic")
                    if not topic_name:
                        continue
                    try:
                        topic_id = await get_or_create_topic(dest, topic_name)
                        await m.forward(chat_id=dest, message_thread_id=topic_id)
                        count += 1
                        await asyncio.sleep(0.3)
                    except Exception:
                        continue
        except Exception:
            continue
    await msg.reply(f"✅ Old scan completed. Forwarded: {count} messages.")

# ----------------- Auto forward for new messages -----------------

@app.on_message(filters.chat(lambda c: True) & (filters.video | filters.document))
async def auto_forward_handler(_, message: Message):
    db = load_db()
    if not db["forward_on"]:
        return
    if message.chat.id not in db["sources"]:
        return
    if not message.caption:
        return
    dest = db["dest"]
    if not dest:
        return
    topic_name = extract_field(message.caption, "Topic")
    if not topic_name:
        return
    try:
        topic_id = await get_or_create_topic(dest, topic_name)
        await message.forward(chat_id=dest, message_thread_id=topic_id)
    except Exception:
        # fallback to copy without thread if something fails
        try:
            await message.copy(dest)
        except Exception:
            pass

@app.on_message(filters.command(["start", "help"]))
async def start_help(_, msg: Message):
    await msg.reply(
        "Auto Topic Forward Bot is running. Owner-only commands: /addsource /removesource /adddest /startforward /stopforward /scanold /status"
    )

if __name__ == '__main__':
    print("Bot starting...")
    app.run()
