import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config.config import config
from handlers.base import register_base_handlers
from handlers.messages import register_message_handlers
from database.database import DatabaseManager
from database.models import MessageType

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_scheduled_message(bot: Bot, message):
    """Invia un messaggio programmato."""
    try:
        # Invia il messaggio in base al tipo
        if message.message_type == MessageType.TEXT:
            sent_message = await bot.send_message(
                chat_id=message.chat_id,
                text=message.text
            )
        elif message.message_type == MessageType.PHOTO:
            sent_message = await bot.send_photo(
                chat_id=message.chat_id,
                photo=message.file_id,
                caption=message.caption
            )
        elif message.message_type == MessageType.VIDEO:
            sent_message = await bot.send_video(
                chat_id=message.chat_id,
                video=message.file_id,
                caption=message.caption
            )
        elif message.message_type == MessageType.DOCUMENT:
            sent_message = await bot.send_document(
                chat_id=message.chat_id,
                document=message.file_id,
                caption=message.caption
            )
        elif message.message_type == MessageType.AUDIO:
            sent_message = await bot.send_audio(
                chat_id=message.chat_id,
                audio=message.file_id,
                caption=message.caption
            )
        elif message.message_type == MessageType.VOICE:
            sent_message = await bot.send_voice(
                chat_id=message.chat_id,
                voice=message.file_id,
                caption=message.caption
            )
        elif message.message_type == MessageType.ANIMATION:
            sent_message = await bot.send_animation(
                chat_id=message.chat_id,
                animation=message.file_id,
                caption=message.caption
            )
        
        # Se richiesto, pinna il messaggio
        if message.pin:
            try:
                await bot.pin_chat_message(
                    chat_id=message.chat_id,
                    message_id=sent_message.message_id,
                    disable_notification=True
                )
            except Exception as e:
                logger.error(f"Errore durante il pin del messaggio: {e}")
        
        # Marca il messaggio come inviato
        DatabaseManager.mark_message_as_sent(message.id)
        logger.info(f"Messaggio programmato {message.id} inviato con successo")
        
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio programmato {message.id}: {e}")

async def check_scheduled_messages(bot: Bot):
    """Controlla e invia i messaggi programmati."""
    while True:
        try:
            # Ottiene i messaggi da inviare
            messages = DatabaseManager.get_pending_messages()
            
            # Invia ogni messaggio
            for message in messages:
                await send_scheduled_message(bot, message)
            
            # Attende 60 secondi prima del prossimo controllo
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Errore durante il controllo dei messaggi programmati: {e}")
            await asyncio.sleep(60)

async def on_startup(bot: Bot, dispatcher: Dispatcher):
    """Funzione chiamata all'avvio del bot."""
    logger.info("Bot avviato!")
    
    try:
        # Registra gli handlers
        register_base_handlers(dispatcher)
        register_message_handlers(dispatcher)
        
        # Crea la tastiera principale
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Invia Messaggio")],
                [KeyboardButton(text="⏰ Messaggi Programmati")],
                [KeyboardButton(text="ℹ️ Info")]
            ],
            resize_keyboard=True
        )
        
        # Notifica l'admin dell'avvio del bot
        await bot.send_message(
            chat_id=config.admin_id,
            text="✅ Bot avviato e pronto all'uso!\n"
                 "Usa i comandi nella tastiera per gestire i messaggi.",
            reply_markup=keyboard
        )
        
        # Avvia il task per controllare i messaggi programmati
        asyncio.create_task(check_scheduled_messages(bot))
        
    except Exception as e:
        logger.error(f"Errore durante l'avvio del bot: {e}")
        raise e

async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    """Funzione chiamata allo spegnimento del bot."""
    logger.info("Bot in chiusura...")
    
    try:
        # Notifica l'admin della chiusura del bot
        await bot.send_message(
            chat_id=config.admin_id,
            text="🔴 Bot in fase di spegnimento...",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Chiudi la storage
        await dispatcher.storage.close()
        
        logger.info("Bot spento correttamente!")
        
    except Exception as e:
        logger.error(f"Errore durante la chiusura del bot: {e}")
        raise e

async def main():
    # Inizializzazione bot e dispatcher
    bot = Bot(token=config.token, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Registra i gestori di avvio e spegnimento
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Avvia il polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot fermato!")