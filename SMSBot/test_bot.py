import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Prendi il token dal config
from config import bot_token, admin_id

# Inizializza bot e dispatcher
bot = Bot(token=bot_token)
dp = Dispatcher()

# Handler semplice per /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"Ricevuto comando start da {message.from_user.id}")
    await message.answer("Bot funzionante! 👋")

# Handler per qualsiasi messaggio
@dp.message()
async def echo(message: types.Message):
    print(f"Ricevuto messaggio: {message.text}")
    await message.answer("Ho ricevuto il tuo messaggio!")

async def main():
    print("Bot in avvio...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Inizializzazione bot...")
    asyncio.run(main())