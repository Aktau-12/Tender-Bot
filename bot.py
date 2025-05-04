import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
import subprocess

# Загружаем .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://tender-bot.onrender.com/webhook")

if not TOKEN:
    raise ValueError("❌ TOKEN is missing! Check your .env file or environment settings.")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Кнопки меню
menu_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Товары')],
    [KeyboardButton(text='Услуги')],
    [KeyboardButton(text='Работы')],
    [KeyboardButton(text='Стоп 🛑')]
], resize_keyboard=True)

process_running = False

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("Привет! 👋 Я бот для поиска тендеров.\nВыбери категорию:", reply_markup=menu_kb)

@dp.message()
async def handle_message(message: types.Message):
    global process_running
    text = message.text.lower()
    if text in ['товары', 'услуги', 'работы']:
        if process_running:
            await message.answer("⚙️ Парсер уже работает, дождись завершения или нажми 'Стоп 🛑'.")
            return
        await message.answer(f"🚀 Запускаю парсер для категории: {text.capitalize()}")
        process_running = True
        try:
            subprocess.run(['python', 'parser.py', text], check=True)
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
                await message.answer("✅ Результаты отправлены!")
            else:
                await message.answer("⚠️ Файл tenders.xlsx не найден.")
        except subprocess.CalledProcessError as e:
            await message.answer(f"❌ Ошибка запуска парсера:\n{e}")
        finally:
            process_running = False
    elif text == 'стоп 🛑':
        if process_running:
            process_running = False
            await message.answer("🛑 Парсер остановлен.\nОтправляю текущие результаты:")
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
            else:
                await message.answer("⚠️ Файл tenders.xlsx не найден.")
        else:
            await message.answer("ℹ️ Парсер сейчас не запущен.")
    else:
        await message.answer("❗ Пожалуйста, выбери категорию с кнопки.", reply_markup=menu_kb)

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

async def main():
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp)
    return app

if __name__ == '__main__':
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv('PORT', 10000)))
