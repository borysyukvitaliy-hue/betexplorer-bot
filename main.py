import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from playwright.async_api import async_playwright

# -----------------------------
# Telegram
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -----------------------------
# Файли
# -----------------------------
KNOWN_MATCHES_FILE = "known_matches.json"
CONFIG_FILE = "config.json"

DEFAULT_FILTERS = {
    "drop_in_last": "24hours",
    "matches_for": "today",
    "dropping_bookies": ">30%"
}

# -----------------------------
# Фільтри
# -----------------------------
def load_filters():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_FILTERS

def save_filters(filters):
    with open(CONFIG_FILE, "w") as f:
        json.dump(filters, f, indent=2)

filters = load_filters()

# -----------------------------
# Telegram команди
# -----------------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот запущено та готовий до роботи!")
    print("[INFO] Бот запущено")

@dp.message(Command("status"))
async def status(message: types.Message):
    await message.answer("✅ Бот працює! Перевірка подій кожні 10 хвилин.")

@dp.message(Command("reset"))
async def reset_data(message: types.Message):
    if os.path.exists(KNOWN_MATCHES_FILE):
        os.remove(KNOWN_MATCHES_FILE)
        await message.answer("🧹 Всі збережені матчі очищено!")
        print("[INFO] known_matches.json очищено через /reset")
    else:
        await message.answer("ℹ️ Файл known_matches.json ще не створено.")

# -----------------------------
# Playwright: скрейпінг з headless=False та логами
# -----------------------------
async def fetch_events():
    events = []
    async with async_playwright() as p:
        # Запускаємо браузер у видимому режимі для дебагу
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print("[INFO] Відкрив сторінку BetExplorer...")
       
        await page.goto("https://www.betexplorer.com/odds-movements/tennis/", timeout=60000)
        print("[INFO] Сторінка завантажена, очікую таблицю подій...")
       
        try:
            await page.wait_for_selector("tr:has(td.table-main__drop)", timeout=15000)
            print("[INFO] Таблиця подій знайдена!")
        except Exception:
            print("[ERROR] Не вдалося знайти таблицю подій")
            await browser.close()
            return []

        rows = await page.query_selector_all("tr:has(td.table-main__drop)")
        for r in rows:
            try:
                match_el = await r.query_selector("td.table-main__tt a")
                drop_el = await r.query_selector("td.table-main__drop")
                match = (await match_el.inner_text()).strip()
                drop = (await drop_el.inner_text()).strip()
                events.append({"match": match, "drop": drop})
            except Exception as e:
                print("[WARN] Пропущено рядок:", e)
                continue

        await browser.close()
    print(f"[INFO] Знайдено подій: {len(events)}")
    return events

# -----------------------------
# Збереження та перевірка подій
# -----------------------------
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
        print(f"[INFO] Нові події: {len(new_events)}")
        for e in new_events:
            msg = f"🎾 {e['match']} | Drop: {e['drop']}"
            await bot.send_message(CHAT_ID, msg)
        save_known_matches(events)
    else:
        print("[INFO] Нових подій немає")

# -----------------------------
# Основний цикл
# -----------------------------
async def main_loop():
    print("[INFO] Бот запущено та моніторить події кожні 10 хв.")
    await bot.send_message(CHAT_ID, "🤖 Бот запущено! Починаю моніторинг...")

    while True:
        try:
            await check_new_events()
        except Exception as e:
            print("[ERROR]", e)
        await asyncio.sleep(600)  # 10 хвилин

# -----------------------------
# Старт
# -----------------------------
async def main():
    loop_task = asyncio.create_task(main_loop())
    await dp.start_polling(bot)
    await loop_task

if __name__ == "__main__":
    asyncio.run(main())
