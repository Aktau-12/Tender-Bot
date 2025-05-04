import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import subprocess
import os

TOKEN = "ТОКЕН_СЮДА"  # замените на свой токен
bot = Bot(token=TOKEN)
dp = Dispatcher()

menu_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Товары')],
    [KeyboardButton(text='Услуги')],
    [KeyboardButton(text='Работы')],
    [KeyboardButton(text='Стоп 🛑')]
], resize_keyboard=True)

process = None

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("👋 Привет! Я бот для поиска тендеров.\nВыбери категорию:", reply_markup=menu_kb)

@dp.message()
async def handle_message(message: types.Message):
    global process

    text = message.text.lower()
    if text in ['товары', 'услуги', 'работы']:
        if process and process.poll() is None:
            await message.answer("⚙️ Парсер уже работает. Дождись завершения или нажми *Стоп 🛑*.", parse_mode='Markdown')
            return

        await message.answer(f"🚀 Запускаю парсер для категории: *{text.capitalize()}*", parse_mode='Markdown')
        open('stop.flag', 'w').close() if os.path.exists('stop.flag') else None  # сброс стоп-файла

        process = subprocess.Popen(['python', 'parser.py', text])
        await asyncio.sleep(3)
        await message.answer("✅ Парсер запущен! Чтобы остановить, нажми *Стоп 🛑*.", parse_mode='Markdown')

    elif text == 'стоп 🛑':
        if process and process.poll() is None:
            open('stop.flag', 'w').close()
            await message.answer("🛑 Останавливаю парсер... Жди завершения.")
            process.wait()
            await asyncio.sleep(2)
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
                await message.answer("✅ Отправил файл Excel с результатами!")
            else:
                await message.answer("⚠️ Файл Excel не найден. Возможно, не было данных.")
        else:
            await message.answer("ℹ️ Парсер сейчас не запущен.")

    else:
        await message.answer("❗ Пожалуйста, выбери категорию с кнопки.", reply_markup=menu_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
