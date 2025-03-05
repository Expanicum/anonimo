import asyncio
import logging
import sys
from datetime import datetime, timedelta
import pytz

# Configura logging dettagliato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

try:
    import nest_asyncio
    nest_asyncio.apply()
    logger.info("nest_asyncio applicato con successo")
except Exception as e:
    logger.error(f"Errore nell'applicazione di nest_asyncio: {e}")
    sys.exit(1)

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.dispatcher.middlewares.base import BaseMiddleware

# Importazione configurazione
try:
    from config import bot_token, admin_id
    logger.info(f"Configurazione caricata con successo. Admin ID: {admin_id}")
except Exception as e:
    logger.error(f"Errore nel caricamento della configurazione: {e}")
    sys.exit(1)

# Verifica token
if not bot_token or len(bot_token) < 45:
    logger.error(f"Token del bot non valido o mancante: {bot_token[:5]}...")
    sys.exit(1)

# Inizializzazione bot e dispatcher
bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Importazione moduli
from keyboards import main_menu_keyboard
from messages import messages_router
from scheduled_messages import scheduled_router, send_scheduled_messages, show_scheduled_menu

class ChatTypeMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            if hasattr(event, "chat") and event.chat:
                data["chat_type"] = event.chat.type
                logger.debug(f"Middleware: chat_type = {event.chat.type}")
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Errore nel middleware: {e}")
            return await handler(event, data)

async def check_scheduled_messages():
    """Controlla periodicamente i messaggi programmati."""
    while True:
        try:
            await send_scheduled_messages()
        except Exception as e:
            logger.error(f"Errore nel controllo dei messaggi programmati: {e}")
        await asyncio.sleep(60)  # Controlla ogni minuto

async def test_bot_connection():
    """Testa la connessione del bot."""
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connesso con successo! Nome: @{bot_info.username}")
        return True
    except Exception as e:
        logger.error(f"Errore nella connessione del bot: {e}")
        return False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Gestisce il comando /start."""
    try:
        user_id = message.from_user.id
        logger.info(f"Comando /start ricevuto da user_id: {user_id}")
        
        if user_id != admin_id:
            logger.warning(f"Tentativo di accesso non autorizzato da user_id: {user_id}")
            await message.answer("⛔ Non sei autorizzato a usare questo bot.")
            return
        
        await message.answer(
            "👋 <b>Benvenuto nel bot di gestione dei messaggi!</b>\n\n"
            "Seleziona un'opzione:",
            reply_markup=main_menu_keyboard()
        )
        logger.info(f"Menu principale inviato con successo a user_id: {user_id}")
    except Exception as e:
        logger.error(f"Errore nel comando start: {e}")
        await message.answer("❌ Si è verificato un errore. Riprova più tardi.")

@dp.callback_query(lambda c: c.data == "menu_messages")
async def menu_messages_callback(callback: CallbackQuery):
    """Gestisce il callback del menu messaggi."""
    try:
        if callback.from_user.id != admin_id:
            await callback.answer("⛔ Non sei autorizzato", show_alert=True)
            return
        
        from messages import show_messages_menu
        await show_messages_menu(callback.message)
        await callback.answer()
    except Exception as e:
        logger.error(f"Errore nel menu messaggi: {e}")
        await callback.message.answer("❌ Si è verificato un errore. Riprova più tardi.")

@dp.callback_query(lambda c: c.data == "menu_scheduled")
async def scheduled_menu_callback(callback: CallbackQuery):
    """Gestisce il callback del menu messaggi programmati."""
    try:
        if callback.from_user.id != admin_id:
            await callback.answer("⛔ Non sei autorizzato", show_alert=True)
            return
        
        await show_scheduled_menu(callback.message)
        await callback.answer()
    except Exception as e:
        logger.error(f"Errore nel menu messaggi programmati: {e}")
        await callback.message.answer("❌ Si è verificato un errore. Riprova più tardi.")

async def main():
    """Funzione principale del bot."""
    try:
        logger.info("🤖 Inizializzazione del bot...")
        
        # Test connessione
        if not await test_bot_connection():
            logger.error("❌ Impossibile connettersi al bot. Verificare il token.")
            return

        # Applicazione middleware
        dp.message.middleware(ChatTypeMiddleware())
        dp.callback_query.middleware(ChatTypeMiddleware())

        # Inclusione router
        dp.include_router(messages_router)
        dp.include_router(scheduled_router)
        
        # Avvio task per il controllo dei messaggi programmati
        asyncio.create_task(check_scheduled_messages())
        
        logger.info("🚀 Avvio del polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"Errore durante l'avvio del bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info("🔄 Avvio del loop principale...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot terminato dall'utente")
    except Exception as e:
        logger.error(f"❌ Errore fatale: {e}")
        sys.exit(1)