import asyncio
import os
import json
import pandas as pd
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ TOKEN or WEBHOOK_URL is missing! Check your .env file or environment settings.")

bot = Bot(token=TOKEN)
dp = Dispatcher()
menu_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Товары')],
    [KeyboardButton(text='Услуги')],
    [KeyboardButton(text='Работы')],
    [KeyboardButton(text='Стоп 🛑')]
], resize_keyboard=True)

process_flag_file = "status.flag"

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("Привет! 👋 Я бот для поиска тендеров.\nВыбери категорию:", reply_markup=menu_kb)

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.lower()
    if text in ['товары', 'услуги', 'работы']:
        if os.path.exists(process_flag_file):
            await message.answer("⚙️ Парсер уже работает, дождись завершения или нажми 'Стоп 🛑'.")
            return

        await message.answer(f"🚀 Запускаю парсер для категории: {text.capitalize()}")
        open(process_flag_file, 'w').close()
        try:
            subprocess.run(['python', 'parser.py', text], check=True)
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
                await message.answer("✅ Результаты отправлены!")
            else:
                await message.answer("⚠️ Файл tenders.xlsx не найден. Возможно, парсер ничего не нашёл.")
        except subprocess.CalledProcessError as e:
            await message.answer(f"❌ Ошибка запуска парсера:\n{e}")
        finally:
            if os.path.exists(process_flag_file):
                os.remove(process_flag_file)

    elif text == 'стоп 🛑':
        if os.path.exists(process_flag_file):
            os.remove(process_flag_file)
            await message.answer("🛑 Парсер остановлен.\nФайл с текущими результатами:")
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
            else:
                await message.answer("⚠️ Файл tenders.xlsx не найден.")
        else:
            await message.answer("ℹ️ Парсер сейчас не запущен.")

    else:
        await message.answer("❗ Пожалуйста, выбери категорию с кнопки.", reply_markup=menu_kb)

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))
