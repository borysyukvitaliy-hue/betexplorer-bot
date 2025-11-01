import os
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask

# ==============================
#  Flask сервер для Render ping
# ==============================
app = Flask(__name__)

@app.route("/")
def alive():
    return "Bot is alive!"

# ==============================
#  Telegram bot
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

KNOWN_MATCHES_FILE = "known_matches.json"
CONFIG_FILE = "config.json"

DEFAULT_FILTERS = {
    "drop_in_last": "24hours",
    "matches_for": "today",
    "dropping_bookies": ">30%"
}

def load_filters():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_FILTERS

def save_filters(filters):
    with open(CONFIG_FILE, "w") as f:
        json.dump(filters, f, indent=2)

filters = load_filters()

# ==============================
#  Telegram commands
# ==============================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот запущено та готовий до роботи!")

@dp.message(Command("status"))
async def status(message: types.Message):
    await message.answer("✅ Бот працює! Перевірка подій кожні 10 хвилин.")

# ==============================
#  Fetch and check events
# ==============================
async def fetch_events():
    url = "https://www.betexplorer.com/odds-movements/tennis/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr:has(td.table-main__drop)")
    events = []
    for r in rows:
        try:
            match = r.select_one("td.table-main__tt a").text.strip()
            drop = r.select_one("td.table-main__drop").text.strip()
            events.append({"match": match, "drop": drop})
        except:
            continue
    return events

def load_known_matches():
    if os.path.exists(KNOWN_MATCHES_FILE):
        with open(KNOWN_MATCHES_FILE, "r") as f:
            return json.load(f)
    return []

def save_known_matches(data):
    with open(KNOWN_MATCHES_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def check_new_events():
    known = load_known_matches()
    events = await fetch_events()
    new_events = [e for e in events if e not in known]
    if new_events:
        for e in new_events:
            msg = f"🎾 {e['match']} | Drop: {e['drop']}"
            await bot.send_message(CHAT_ID, msg)
        save_known_matches(events)

# ==============================
#  Main loop
# ==============================
async def main_loop():
    while True:
        try:
            await check_new_events()
        except Exception as e:
            print("[ERROR]", e)
        await asyncio.sleep(600)  # 10 хв

async def main():
    loop_task = asyncio.create_task(main_loop())
    await dp.start_polling(bot)
    await loop_task

# ==============================
#  Run Flask + Telegram
# ==============================
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    asyncio.run(main())
