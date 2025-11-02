import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

URL = "https://www.betexplorer.com/next/soccer/"


async def get_matches():
    print("🧠 [DEBUG] Запускаю Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print("✅ [DEBUG] Chromium запущено")

        context = await browser.new_context()
        page = await context.new_page()

        print(f"🌍 [DEBUG] Відкриваю сторінку: {URL}")
        try:
            await page.goto(URL, timeout=30000)
        except Exception as e:
            print(f"❌ [DEBUG] Не вдалося завантажити сторінку: {e}")
            await browser.close()
            return []

        print("📄 [DEBUG] Сторінка завантажена, шукаю події...")
        try:
            # Залежно від верстки: заміни селектор, якщо потрібно
            matches = await page.query_selector_all(".in-match")
            print(f"🎯 [DEBUG] Знайдено {len(matches)} елементів .in-match")
        except Exception as e:
            print(f"⚠️ [DEBUG] Помилка під час пошуку подій: {e}")
            matches = []

        await browser.close()
        print("🚪 [DEBUG] Браузер закрито")

        return matches


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Бот запущено, шукаю події...")
    matches = await get_matches()

    if not matches:
        await message.answer("😕 Подій не знайдено (можливо, змінилась верстка або сторінка недоступна).")
    else:
        await message.answer(f"✅ Знайдено {len(matches)} подій!")


async def main():
    print("🤖 [DEBUG] Бот запускається...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
