import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import subprocess

# Загружаем .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
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

# Состояние парсера
process_running = False

# Команда /start
@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("Привет! 👋 Я бот для поиска тендеров.\nВыбери категорию:", reply_markup=menu_kb)

# Обработка кнопок
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
            # Запуск parser.py с категорией
            subprocess.run(['python', 'parser.py', text], check=True)

            # Проверка и отправка Excel файла
            if os.path.exists('tenders.xlsx'):
                with open('tenders.xlsx', 'rb') as file:
                    await bot.send_document(message.chat.id, file)
                await message.answer("✅ Результаты отправлены!")
            else:
                await message.answer("⚠️ Файл tenders.xlsx не найден. Возможно, парсер ничего не нашёл.")
        except subprocess.CalledProcessError as e:
            await message.answer(f"❌ Ошибка запуска парсера:\n{e}")
        finally:
            process_running = False

    elif text == 'стоп 🛑':
        if process_running:
            process_running = False
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

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
