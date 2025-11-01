import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from playwright.async_api import async_playwright

# =============================
# Telegram
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =============================
# Файли для збереження стану
# =============================
KNOWN_MATCHES_FILE = "known_matches.json"
CONFIG_FILE = "config.json"

DEFAULT_FILTERS = {
    "drop_in_last": "24hours",
    "matches_for": "today",
    "dropping_bookies": ">30%"
}

# -------------------------------------
# Завантаження та збереження фільтрів
# -------------------------------------
def load_filters():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_FILTERS

def save_filters(filters):
    with open(CONFIG_FILE, "w") as f:
        json.dump(filters, f, indent=2)

filters = load_filters()

# -------------------------------------
# Telegram команди
# -------------------------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот запущено та готовий до роботи!")
    print("[INFO] Бот запущено")

@dp.message(Command("status"))
async def status(message: types.Message):
    await message.answer("✅ Бот працює! Перевірка подій кожні 10 хвилин.")

@dp.message(Command("filters"))
async def show_filters(message: types.Message):
    kb = [
        [
            types.InlineKeyboardButton(text="1h", callback_data="drop_1hour"),
            types.InlineKeyboardButton(text="2h", callback_data="drop_2hours"),
            types.InlineKeyboardButton(text="12h", callback_data="drop_12hours"),
            types.InlineKeyboardButton(text="24h ✅", callback_data="drop_24hours"),
            types.InlineKeyboardButton(text="48h", callback_data="drop_48hours")
        ],
        [
            types.InlineKeyboardButton(text="today", callback_data="match_today"),
            types.InlineKeyboardButton(text="today & tomorrow", callback_data="match_today_tomorrow"),
            types.InlineKeyboardButton(text="7 days", callback_data="match_7days"),
            types.InlineKeyboardButton(text="anytime", callback_data="match_anytime")
        ],
        [
            types.InlineKeyboardButton(text=">30%", callback_data="book_30"),
            types.InlineKeyboardButton(text=">40%", callback_data="book_40"),
            types.InlineKeyboardButton(text=">50%", callback_data="book_50"),
            types.InlineKeyboardButton(text=">60%", callback_data="book_60"),
            types.InlineKeyboardButton(text=">70%", callback_data="book_70")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

    text = (
        f"⚙️ Поточні фільтри:\n"
        f"• Drop in last: {filters['drop_in_last']}\n"
        f"• Matches for: {filters['matches_for']}\n"
        f"• Dropping bookies: {filters['dropping_bookies']}"
    )
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query()
async def change_filter(callback: types.CallbackQuery):
    data = callback.data

    if data.startswith("drop_"):
        filters["drop_in_last"] = data.replace("drop_", "")
    elif data.startswith("match_"):
        val = data.replace("match_", "")
        mapping = {
            "today": "today",
            "today_tomorrow": "today & tomorrow",
            "7days": "next 7 days",
            "anytime": "anytime"
        }
        filters["matches_for"] = mapping.get(val, "today")
    elif data.startswith("book_"):
        filters["dropping_bookies"] = f">{data.replace('book_', '')}%"

    save_filters(filters)
    await callback.answer("✅ Фільтри оновлено!")
    await callback.message.edit_text(
        f"🔄 Нові фільтри:\n"
        f"• Drop in last: {filters['drop_in_last']}\n"
        f"• Matches for: {filters['matches_for']}\n"
        f"• Dropping bookies: {filters['dropping_bookies']}"
    )
    print("[INFO] Фільтри змінено:", filters)

# -------------------------------------
# /reset - очищення відомих матчів
# -------------------------------------
@dp.message(Command("reset"))
async def reset_data(message: types.Message):
    if os.path.exists(KNOWN_MATCHES_FILE):
        os.remove(KNOWN_MATCHES_FILE)
        await message.answer("🧹 Всі збережені матчі очищено! Бот почне з чистого списку.")
        print("[INFO] known_matches.json очищено вручну через /reset")
    else:
        await message.answer("ℹ️ Файл known_matches.json ще не створено, нічого очищати.")
        print("[INFO] /reset викликано, але файл не існує.")

# -------------------------------------
# Завантаження/збереження відомих матчів
# -------------------------------------
def load_known_matches():
    if os.path.exists(KNOWN_MATCHES_FILE):
        with open(KNOWN_MATCHES_FILE, "r") as f:
            return json.load(f)
    return []

def save_known_matches(data):
    with open(KNOWN_MATCHES_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------------------
# Функція отримання подій через Playwright + XPath
# -------------------------------------
async def fetch_events():
    url = "https://www.betexplorer.com/odds-movements/tennis/"
    print("[INFO] Запускаю браузер Playwright та отримую дані з сайту...")
    events = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)  # 30 сек таймаут

        try:
            await page.wait_for_selector("//tr[td[contains(text(), '%')]]", timeout=15000)
        except:
            print("[WARN] Не знайдено подій на сторінці")
            await browser.close()
            return events

        rows = await page.query_selector_all("//tr[td[contains(text(), '%')]]")
        for r in rows:
            try:
                match_el = await r.query_selector(".//td[1]//a")
                drop_el = await r.query_selector(".//td[contains(text(), '%')]")
                match_name = await match_el.inner_text()
                drop = await drop_el.inner_text()
                events.append({"match": match_name.strip(), "drop": drop.strip()})
            except Exception:
                continue

        await browser.close()

    print(f"[INFO] Знайдено подій: {len(events)}")
    return events

# -------------------------------------
# Перевірка нових подій
# -------------------------------------
async def check_new_events():
    known = load_known_matches()
    events = await fetch_events()

    new_events = [e for e in events if e not in known]

    if new_events:
        print(f"[INFO] Нові події: {len(new_events)}")
        for e in new_events:
            msg = f"🎾 {e['match']} | Drop: {e['drop']}"
            await bot.send_message(CHAT_ID, msg)
        save_known_matches(events)
    else:
        print("[INFO] Нових подій немає")

# -------------------------------------
# Цикл перевірки подій
# -------------------------------------
async def main_loop():
    print("[INFO] Бот запущено та моніторить події кожні 10 хв.")
    await bot.send_message(CHAT_ID, "🤖 Бот запущено! Починаю моніторинг...")

    while True:
        try:
            await check_new_events()
        except Exception as e:
            print("[ERROR]", e)
        await asyncio.sleep(600)  # 10 хв

# -------------------------------------
# Запуск бота
# -------------------------------------
async def main():
    loop_task = asyncio.create_task(main_loop())
    await dp.start_polling(bot)
    await loop_task

if __name__ == "__main__":
    asyncio.run(main())
