import os
import asyncio
import logging
import sys
import signal
import functools
from datetime import datetime, timedelta
import pytz
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from database.database import DatabaseManager
from database.models import MessageType, RecurrenceType
from keyboards import (
    main_menu_keyboard,
    groups_keyboard,
    schedule_groups_keyboard,
    pin_keyboard,
    schedule_pin_keyboard,
    message_actions_keyboard,
    schedule_type_keyboard,
    weekdays_keyboard,
    messages_filter_keyboard,
    message_details_keyboard,
    confirmation_keyboard
)

# Carica variabili d'ambiente
load_dotenv()

# Setup base
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
MEDIA_DIR = BASE_DIR / "media"
DB_DIR = BASE_DIR / "database"

for dir_path in [LOGS_DIR, MEDIA_DIR, DB_DIR]:
    dir_path.mkdir(exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Costanti dalle variabili d'ambiente
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
GRUPPO_1_ID = int(os.getenv('GRUPPO_1_ID', 0))
GRUPPO_2_ID = int(os.getenv('GRUPPO_2_ID', 0))
GRUPPO_1_NAME = os.getenv('GRUPPO_1_NAME', 'Clienti')  # Valore default se non trovato
GRUPPO_2_NAME = os.getenv('GRUPPO_2_NAME', 'Reseller') # Valore default se non trovato

# Stati FSM
class States(StatesGroup):
    # Stati per messaggi immediati
    WAITING_GROUP = State()
    WAITING_MESSAGE = State()
    WAITING_PIN = State()
    
    # Stati per messaggi schedulati
    SCHEDULE_WAITING_GROUP = State()
    SCHEDULE_WAITING_TYPE = State()
    SCHEDULE_WAITING_TIME = State()
    SCHEDULE_WAITING_DAYS = State()
    SCHEDULE_WAITING_MESSAGE = State()
    SCHEDULE_WAITING_PIN = State()
    
    # Stati per gestione lista messaggi
    VIEWING_MESSAGE = State()
    CONFIRMING_DELETE = State()
    FILTERING_MESSAGES = State()

# Messaggi
MESSAGES = {
    'welcome': f'👋 Benvenuto Admin nel bot di gestione messaggi!\n\nSeleziona un\'opzione:',
    'unauthorized': '⛔️ Non sei autorizzato ad utilizzare questo bot.',
    'error': '❌ Si è verificato un errore. Riprova più tardi.',
    'delete_confirm': '⚠️ Sei sicuro di voler eliminare questo messaggio? Questa azione non può essere annullata.',
    'deleted': '✅ Messaggio eliminato con successo.',
    'toggled': '✅ Stato del messaggio aggiornato.',
    'not_found': '❌ Messaggio non trovato.'
}

# Init bot
storage = MemoryStorage()
dp = None
bot = None

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_group_name(chat_id: int) -> str:
    if chat_id == GRUPPO_1_ID:
        return GRUPPO_1_NAME
    elif chat_id == GRUPPO_2_ID:
        return GRUPPO_2_NAME
    return "Entrambi i gruppi"

# HANDLERS PER MESSAGGI IMMEDIATI
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(MESSAGES['unauthorized'])
        return
    
    current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
    welcome_msg = f"{MESSAGES['welcome']}\n\nData/Ora attuale (UTC): {current_time}"
    await message.answer(welcome_msg, reply_markup=main_menu_keyboard())

async def send_message_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return
    await state.set_state(States.WAITING_GROUP)
    await callback.message.edit_text(
        "📤 Seleziona il gruppo dove inviare il messaggio:", 
        reply_markup=groups_keyboard()
    )
    await callback.answer()

async def group_selection_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    chat_ids = None
    if callback.data == "group_1":
        chat_ids = GRUPPO_1_ID
    elif callback.data == "group_2":
        chat_ids = GRUPPO_2_ID
    elif callback.data == "group_both":
        chat_ids = [GRUPPO_1_ID, GRUPPO_2_ID]
    
    await state.update_data(chat_id=chat_ids)
    await state.set_state(States.WAITING_MESSAGE)
    await callback.message.edit_text("📝 Invia il messaggio da inviare:")
    await callback.answer()

async def process_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    await state.update_data(
        message_text=message.text,
        message_photo=message.photo[-1].file_id if message.photo else None,
        message_video=message.video.file_id if message.video else None,
        message_document=message.document.file_id if message.document else None,
        message_caption=message.caption
    )
    
    await state.set_state(States.WAITING_PIN)
    await message.answer("📌 Vuoi pinnare questo messaggio?", reply_markup=pin_keyboard())

async def process_pin(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    data = await state.get_data()
    chat_ids = data['chat_id']
    should_pin = callback.data == "pin_yes"

    if not isinstance(chat_ids, list):
        chat_ids = [chat_ids]

    try:
        for chat_id in chat_ids:
            sent_message = None
            if data.get('message_text'):
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=data['message_text']
                )
            elif data.get('message_photo'):
                sent_message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=data['message_photo'],
                    caption=data.get('message_caption')
                )
            elif data.get('message_video'):
                sent_message = await bot.send_video(
                    chat_id=chat_id,
                    video=data['message_video'],
                    caption=data.get('message_caption')
                )
            elif data.get('message_document'):
                sent_message = await bot.send_document(
                    chat_id=chat_id,
                    document=data['message_document'],
                    caption=data.get('message_caption')
                )

            if should_pin and sent_message:
                await bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=sent_message.message_id
                )

        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        await callback.message.edit_text(
            f"✅ Messaggio inviato con successo!\nInviato il: {current_time} UTC",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Errore invio: {e}")
        await callback.message.edit_text(
            MESSAGES['error'],
            reply_markup=main_menu_keyboard()
        )

    await state.clear()
    await callback.answer()

# HANDLERS PER MESSAGGI SCHEDULATI
async def schedule_start_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return
    
    await state.set_state(States.SCHEDULE_WAITING_GROUP)
    await callback.message.edit_text(
        "📅 Seleziona il gruppo dove programmare il messaggio:",
        reply_markup=schedule_groups_keyboard()
    )
    await callback.answer()

async def schedule_group_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    group_id = callback.data.replace("schedule_to_", "")
    chat_ids = None
    
    if group_id == "1":
        chat_ids = GRUPPO_1_ID
    elif group_id == "2":
        chat_ids = GRUPPO_2_ID
    elif group_id == "both":
        chat_ids = [GRUPPO_1_ID, GRUPPO_2_ID]
    
    await state.update_data(schedule_chat_id=chat_ids)
    await state.set_state(States.SCHEDULE_WAITING_TYPE)
    await callback.message.edit_text(
        "📋 Seleziona il tipo di programmazione:",
        reply_markup=schedule_type_keyboard()
    )
    await callback.answer()

async def schedule_type_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    schedule_type = callback.data.replace("schedule_type_", "")
    await state.update_data(schedule_type=schedule_type)
    
    if schedule_type == "weekly":
        await state.set_state(States.SCHEDULE_WAITING_DAYS)
        await callback.message.edit_text(
            "📆 Seleziona i giorni in cui inviare il messaggio:",
            reply_markup=weekdays_keyboard()
        )
    else:
        await state.set_state(States.SCHEDULE_WAITING_TIME)
        current_time = datetime.now(pytz.UTC).strftime('%H:%M')
        await callback.message.edit_text(
            f"🕒 Invia l'orario di invio nel formato HH:MM\n"
            f"Esempio: {current_time}\n"
            f"Ora attuale (UTC): {current_time}"
        )
    
    await callback.answer()

async def schedule_days_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    selected_days = data.get('selected_days', [])
    
    if callback.data == "days_confirm":
        if not selected_days:
            await callback.answer("⚠️ Seleziona almeno un giorno!", show_alert=True)
            return
        
        await state.set_state(States.SCHEDULE_WAITING_TIME)
        current_time = datetime.now(pytz.UTC).strftime('%H:%M')
        await callback.message.edit_text(
            f"🕒 Invia l'orario di invio nel formato HH:MM\n"
            f"Esempio: {current_time}\n"
            f"Ora attuale (UTC): {current_time}"
        )
    else:
        day = callback.data.replace("day_", "")
        if day in selected_days:
            selected_days.remove(day)
        else:
            selected_days.append(day)
        
        await state.update_data(selected_days=selected_days)
        await callback.message.edit_text(
            "📆 Seleziona i giorni in cui inviare il messaggio:",
            reply_markup=weekdays_keyboard(selected_days)
        )
    
    await callback.answer()

async def process_schedule_time(message: Message, state: FSMContext):
    """Gestisce l'input dell'orario per i messaggi programmati."""
    if not is_admin(message.from_user.id):
        return

    try:
        # Valida formato HH:MM
        time_parts = message.text.strip().split(':')
        if len(time_parts) != 2:
            raise ValueError
            
        hour, minute = map(int, time_parts)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        
        await state.update_data(schedule_hour=hour, schedule_minute=minute)
        
        data = await state.get_data()
        schedule_type = data.get('schedule_type')
        
        # Crea il primo orario di invio
        now = datetime.now(pytz.UTC)
        first_send_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Se l'orario è già passato per oggi, sposta al giorno successivo
        if first_send_time <= now:
            first_send_time += timedelta(days=1)
            
        if schedule_type == 'weekly':
            selected_days = data.get('selected_days', [])
            if not selected_days:
                await message.answer("⚠️ Errore: nessun giorno selezionato. Riprova.")
                return
                
            # Trova il primo giorno valido per l'invio
            current_weekday = now.strftime('%a').lower()
            days_to_add = 0
            
            # Ordina i giorni partendo da oggi
            week_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            current_day_index = week_days.index(current_weekday)
            ordered_days = week_days[current_day_index:] + week_days[:current_day_index]
            
            # Trova il primo giorno selezionato dopo oggi
            for day in ordered_days:
                if day in selected_days:
                    if days_to_add > 0 or first_send_time > now:
                        first_send_time = first_send_time + timedelta(days=days_to_add)
                        break
                days_to_add += 1
                
            if days_to_add >= 7:
                first_send_time = first_send_time + timedelta(days=(7 - days_to_add))

        await state.update_data(first_send_time=first_send_time)
        await state.set_state(States.SCHEDULE_WAITING_MESSAGE)
        await message.answer(
            "📝 Perfetto! Ora invia il messaggio da programmare:"
        )
        
    except ValueError:
        current_time = datetime.now(pytz.UTC).strftime('%H:%M')
        await message.answer(
            f"⚠️ Formato orario non valido.\n"
            f"Usa il formato: HH:MM\n"
            f"Esempio: {current_time}\n"
            f"Ora attuale (UTC): {current_time}"
        )

async def process_scheduled_message(message: Message, state: FSMContext):
    """Gestisce il messaggio da programmare dopo aver impostato l'orario."""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    if not data.get('first_send_time'):
        await message.answer("⚠️ Errore: orario non impostato. Riprova dall'inizio.")
        await state.clear()
        return

    await state.update_data(
        schedule_text=message.text,
        schedule_photo=message.photo[-1].file_id if message.photo else None,
        schedule_video=message.video.file_id if message.video else None,
        schedule_document=message.document.file_id if message.document else None,
        schedule_caption=message.caption
    )
    
    await state.set_state(States.SCHEDULE_WAITING_PIN)
    await message.answer(
        "📌 Vuoi che il messaggio venga pinnato quando sarà inviato?",
        reply_markup=schedule_pin_keyboard()
    )

async def process_schedule_pin(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    data = await state.get_data()
    should_pin = callback.data == "schedule_pin_yes"
    chat_ids = data['schedule_chat_id']
    
    if not isinstance(chat_ids, list):
        chat_ids = [chat_ids]

    try:
        for chat_id in chat_ids:
            message_data = {
                'chat_id': chat_id,
                'send_time': data['first_send_time'],
                'pin': should_pin,
                'active': True,
                'recurrence_type': data['schedule_type'],
                'recurrence_days': ','.join(data.get('selected_days', [])),
                'schedule_hour': data['schedule_hour'],
                'schedule_minute': data['schedule_minute']
            }

            if data.get('schedule_text'):
                message_data.update({
                    'message_type': MessageType.TEXT,
                    'text': data['schedule_text']
                })
            elif data.get('schedule_photo'):
                message_data.update({
                    'message_type': MessageType.PHOTO,
                    'media': data['schedule_photo'],
                    'caption': data.get('schedule_caption')
                })
            elif data.get('schedule_video'):
                message_data.update({
                    'message_type': MessageType.VIDEO,
                    'media': data['schedule_video'],
                    'caption': data.get('schedule_caption')
                })
            elif data.get('schedule_document'):
                message_data.update({
                    'message_type': MessageType.DOCUMENT,
                    'media': data['schedule_document'],
                    'caption': data.get('schedule_caption')
                })

            DatabaseManager.add_scheduled_message(message_data)

        schedule_type = data['schedule_type']
        days_map = {
            'mon': 'Lunedì',
            'tue': 'Martedì',
            'wed': 'Mercoledì',
            'thu': 'Giovedì',
            'fri': 'Venerdì',
            'sat': 'Sabato',
            'sun': 'Domenica'
        }
        
        if schedule_type == 'once':
            time_str = data['first_send_time'].strftime('%Y-%m-%d %H:%M')
            msg = f"✅ Messaggio programmato per: {time_str}"
        elif schedule_type == 'daily':
            msg = f"✅ Messaggio programmato ogni giorno alle {data['schedule_hour']:02d}:{data['schedule_minute']:02d}"
        else:  # weekly
            days = data.get('selected_days', [])
            days_str = ', '.join(days_map[day] for day in days)
            msg = f"✅ Messaggio programmato per {days_str} alle {data['schedule_hour']:02d}:{data['schedule_minute']:02d}"
        
        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        msg += f"\n\nProgrammato il: {current_time} UTC"
        
        await callback.message.edit_text(msg, reply_markup=main_menu_keyboard())
    except Exception as e:
        logger.error(f"Errore programmazione: {e}")
        await callback.message.edit_text(
            MESSAGES['error'],
            reply_markup=main_menu_keyboard()
        )

    await state.clear()
    await callback.answer()

# HANDLERS PER LISTA MESSAGGI
async def list_messages_handler(callback: CallbackQuery, state: FSMContext):
    """Handler principale per la lista messaggi."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return
    
    await state.set_state(States.FILTERING_MESSAGES)
    current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
    
    await callback.message.edit_text(
        f"📋 Seleziona il gruppo di cui vuoi vedere i messaggi:\n\n"
        f"Data/Ora attuale (UTC): {current_time}",
        reply_markup=messages_filter_keyboard()
    )
    await callback.answer()

async def filter_messages_handler(callback: CallbackQuery, state: FSMContext):
    """Gestisce il filtro dei messaggi per gruppo."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    filter_type = callback.data.replace("filter_", "")
    chat_id = None
    
    if filter_type == "group1":
        chat_id = GRUPPO_1_ID
    elif filter_type == "group2":
        chat_id = GRUPPO_2_ID
    
    messages = DatabaseManager.get_filtered_messages(chat_id)
    await show_messages_list(callback.message, messages, filter_type)
    await callback.answer()

async def show_messages_list(message: Message, messages: list, filter_type: str):
    """Mostra la lista dei messaggi filtrati."""
    if not messages:
        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        await message.edit_text(
            f"📋 Nessun messaggio programmato per questo gruppo.\n\n"
            f"Data/Ora attuale (UTC): {current_time}",
            reply_markup=messages_filter_keyboard()
        )
        return

    # Organizziamo i messaggi per tipo
    once_messages = []
    daily_messages = []
    weekly_messages = []
    
    days_map = {
        'mon': 'Lunedì',
        'tue': 'Martedì',
        'wed': 'Mercoledì',
        'thu': 'Giovedì',
        'fri': 'Venerdì',
        'sat': 'Sabato',
        'sun': 'Domenica'
    }

    for msg in messages:
        group_name = get_group_name(msg.chat_id)
        msg_info = {
            'id': msg.id,
            'status': "✅" if msg.active else "❌",
            'pin': "📌" if msg.pin else "",
            'type': "📝" if msg.message_type == MessageType.TEXT else (
                   "📷" if msg.message_type == MessageType.PHOTO else (
                   "🎥" if msg.message_type == MessageType.VIDEO else "📎")),
            'group': group_name
        }

        if msg.recurrence_type == 'once':
            msg_info['time'] = msg.send_time.strftime('%Y-%m-%d %H:%M')
            once_messages.append(msg_info)
        elif msg.recurrence_type == 'daily':
            msg_info['time'] = f"{msg.schedule_hour:02d}:{msg.schedule_minute:02d}"
            daily_messages.append(msg_info)
        else:  # weekly
            days = msg.recurrence_days.split(',')
            days_str = ', '.join(days_map[day] for day in days)
            msg_info['time'] = f"{msg.schedule_hour:02d}:{msg.schedule_minute:02d}"
            msg_info['days'] = days_str
            weekly_messages.append(msg_info)

    # Creiamo il messaggio
    group_filter = {
        "group1": GRUPPO_1_NAME,
        "group2": GRUPPO_2_NAME,
        "all": "tutti i gruppi"
    }
    
    text = f"📋 Lista Messaggi - {group_filter.get(filter_type, 'tutti i gruppi')}\n\n"
    
    if once_messages:
        text += "🔹 MESSAGGI SINGOLI:\n"
        for msg in once_messages:
            text += (f"ID: {msg['id']} {msg['status']} {msg['pin']} {msg['type']}\n"
                    f"👥 {msg['group']}\n"
                    f"📅 {msg['time']}\n\n")
    
    if daily_messages:
        text += "🔹 MESSAGGI GIORNALIERI:\n"
        for msg in daily_messages:
            text += (f"ID: {msg['id']} {msg['status']} {msg['pin']} {msg['type']}\n"
                    f"👥 {msg['group']}\n"
                    f"⏰ Ogni giorno alle {msg['time']}\n\n")
    
    if weekly_messages:
        text += "🔹 MESSAGGI SETTIMANALI:\n"
        for msg in weekly_messages:
            text += (f"ID: {msg['id']} {msg['status']} {msg['pin']} {msg['type']}\n"
                    f"👥 {msg['group']}\n"
                    f"📆 {msg['days']}\n⏰ Alle {msg['time']}\n\n")

    current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
    text += f"\nData/Ora attuale (UTC): {current_time}"

    try:
        await message.edit_text(
            text, 
            reply_markup=message_details_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        # Se il messaggio è troppo lungo, lo dividiamo in più parti
        chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:  # Ultimo chunk
                await message.answer(chunk, reply_markup=message_details_keyboard())
            else:
                await message.answer(chunk)

async def view_message_details(callback: CallbackQuery, state: FSMContext):
    """Handler per vedere i dettagli di un messaggio specifico."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    await state.set_state(States.VIEWING_MESSAGE)
    await callback.message.edit_text(
        "🔍 Inserisci l'ID del messaggio che vuoi visualizzare:",
        reply_markup=message_actions_keyboard()
    )
    await callback.answer()

async def process_message_details(message: Message, state: FSMContext):
    """Processa la richiesta di dettagli per un messaggio specifico."""
    if not is_admin(message.from_user.id):
        return

    try:
        msg_id = int(message.text)
        msg = DatabaseManager.get_message_by_id(msg_id)
        
        if not msg:
            await message.answer(
                f"{MESSAGES['not_found']}\n"
                "Inserisci un ID valido o torna alla lista messaggi.",
                reply_markup=message_actions_keyboard()
            )
            return

        # Prepara il testo dettagliato
        text = f"🔍 Dettagli Messaggio #{msg.id}\n\n"
        text += f"Stato: {'✅ Attivo' if msg.active else '❌ Inattivo'}\n"
        text += f"Gruppo: {get_group_name(msg.chat_id)}\n"
        text += f"Pin: {'📌 Sì' if msg.pin else '❌ No'}\n"
        text += f"Tipo: {msg.message_type.name}\n\n"
        
        if msg.message_type == MessageType.TEXT:
            preview = msg.text[:500] + "..." if len(msg.text) > 500 else msg.text
            text += f"Contenuto:\n{preview}\n\n"
        else:
            if msg.caption:
                preview = msg.caption[:200] + "..." if len(msg.caption) > 200 else msg.caption
                text += f"Didascalia:\n{preview}\n\n"
        
        if msg.recurrence_type == 'once':
            text += f"Data/Ora invio: {msg.send_time.strftime('%Y-%m-%d %H:%M')}\n"
        else:
            text += f"Orario invio: {msg.schedule_hour:02d}:{msg.schedule_minute:02d}\n"
            
            if msg.recurrence_type == 'weekly':
                days_map = {
                    'mon': 'Lunedì',
                    'tue': 'Martedì',
                    'wed': 'Mercoledì',
                    'thu': 'Giovedì',
                    'fri': 'Venerdì',
                    'sat': 'Sabato',
                    'sun': 'Domenica'
                }
                days = msg.recurrence_days.split(',')
                days_str = ', '.join(days_map[day] for day in days)
                text += f"Giorni: {days_str}\n"

        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        text += f"\nData/Ora attuale (UTC): {current_time}"

        # Crea la tastiera per le azioni specifiche del messaggio
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Attiva/Disattiva",
                    callback_data=f"toggle_{msg.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Elimina",
                    callback_data=f"delete_{msg.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Torna alla Lista",
                    callback_data="list_messages"
                )
            ]
        ])

        # Se c'è un media, aggiungiamo l'anteprima
        if msg.message_type != MessageType.TEXT:
            try:
                if msg.message_type == MessageType.PHOTO:
                    await message.answer_photo(
                        photo=msg.media,
                        caption=text,
                        reply_markup=keyboard
                    )
                elif msg.message_type == MessageType.VIDEO:
                    await message.answer_video(
                        video=msg.media,
                        caption=text,
                        reply_markup=keyboard
                    )
                elif msg.message_type == MessageType.DOCUMENT:
                    await message.answer_document(
                        document=msg.media,
                        caption=text,
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Errore nell'invio del media: {e}")
                await message.answer(
                    text + "\n\n⚠️ Non è stato possibile mostrare l'anteprima del media.",
                    reply_markup=keyboard
                )
        else:
            await message.answer(text, reply_markup=keyboard)
        
    except ValueError:
        await message.answer(
            "⚠️ ID non valido. Inserisci un numero.",
            reply_markup=message_actions_keyboard()
        )

async def toggle_message_handler(callback: CallbackQuery):
    """Handler per attivare/disattivare un messaggio."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    try:
        msg_id = int(callback.data.split('_')[1])
        success = DatabaseManager.toggle_message(msg_id)
        
        if success:
            await callback.answer(MESSAGES['toggled'], show_alert=True)
            text = callback.message.text
            # Aggiorna lo stato nel testo
            text = text.replace("✅ Attivo", "❌ Inattivo") if "✅ Attivo" in text else text.replace("❌ Inattivo", "✅ Attivo")
            await callback.message.edit_text(
                text,
                reply_markup=callback.message.reply_markup
            )
        else:
            await callback.answer(MESSAGES['not_found'], show_alert=True)
    
    except Exception as e:
        logger.error(f"Errore nel toggle del messaggio: {e}")
        await callback.answer(MESSAGES['error'], show_alert=True)

async def delete_message_handler(callback: CallbackQuery, state: FSMContext):
    """Handler per eliminare un messaggio."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    try:
        msg_id = int(callback.data.split('_')[1])
        msg = DatabaseManager.get_message_by_id(msg_id)
        
        if not msg:
            await callback.answer(MESSAGES['not_found'], show_alert=True)
            return
        
        await state.update_data(delete_msg_id=msg_id)
        await state.set_state(States.CONFIRMING_DELETE)
        
        await callback.message.edit_text(
            f"{MESSAGES['delete_confirm']}\n\n"
            f"ID Messaggio: {msg_id}\n"
            f"Gruppo: {get_group_name(msg.chat_id)}\n"
            f"Tipo: {msg.message_type.name}",
            reply_markup=confirmation_keyboard(msg_id)
        )
        
    except Exception as e:
        logger.error(f"Errore nella preparazione eliminazione: {e}")
        await callback.answer(MESSAGES['error'], show_alert=True)

async def confirm_delete_handler(callback: CallbackQuery, state: FSMContext):
    """Handler per confermare l'eliminazione di un messaggio."""
    if not is_admin(callback.from_user.id):
        await callback.answer(MESSAGES['unauthorized'], show_alert=True)
        return

    if callback.data == "cancel_delete":
        await state.clear()
        await list_messages_handler(callback, state)
        return

    try:
        msg_id = int(callback.data.split('_')[2])
        success = DatabaseManager.delete_message(msg_id)
        
        if success:
            await callback.answer(MESSAGES['deleted'], show_alert=True)
            await list_messages_handler(callback, state)
        else:
            await callback.answer(MESSAGES['not_found'], show_alert=True)
            await state.clear()
    
    except Exception as e:
        logger.error(f"Errore nell'eliminazione: {e}")
        await callback.answer(MESSAGES['error'], show_alert=True)
        await state.clear()

async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handler per tornare al menu principale."""
    try:
        # Pulisci lo stato corrente
        await state.clear()
        
        # Modifica il messaggio esistente con il menu principale
        await callback.message.edit_text(
            "🔄 Menu Principale",
            reply_markup=main_menu_keyboard()
        )
        
        # Rispondi al callback per rimuovere il loading
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Errore nel ritorno al menu principale: {e}")
        await callback.answer("⚠️ Si è verificato un errore. Riprova.", show_alert=True)

# Scheduler con gestione errori migliorata
async def scheduler():
    retry_delay = 5  # secondi di attesa tra i tentativi in caso di errore
    max_retries = 3  # numero massimo di tentativi per messaggio
    
    while True:
        try:
            current_time = datetime.now(pytz.UTC)
            messages = DatabaseManager.get_pending_messages()
            
            for message in messages:
                if message.send_time <= current_time and message.active:
                    for attempt in range(max_retries):
                        try:
                            sent_message = None
                            if message.message_type == MessageType.TEXT:
                                sent_message = await bot.send_message(
                                    chat_id=message.chat_id,
                                    text=message.text
                                )
                            elif message.message_type == MessageType.PHOTO:
                                sent_message = await bot.send_photo(
                                    chat_id=message.chat_id,
                                    photo=message.media,
                                    caption=message.caption
                                )
                            elif message.message_type == MessageType.VIDEO:
                                sent_message = await bot.send_video(
                                    chat_id=message.chat_id,
                                    video=message.media,
                                    caption=message.caption
                                )
                            elif message.message_type == MessageType.DOCUMENT:
                                sent_message = await bot.send_document(
                                    chat_id=message.chat_id,
                                    document=message.media,
                                    caption=message.caption
                                )

                            if message.pin and sent_message:
                                await bot.pin_chat_message(
                                    chat_id=message.chat_id,
                                    message_id=sent_message.message_id
                                )

                            # Gestisci ricorrenza
                            if message.recurrence_type != 'once':
                                next_time = None
                                
                                if message.recurrence_type == 'daily':
                                    next_time = message.send_time + timedelta(days=1)
                                
                                elif message.recurrence_type == 'weekly':
                                    days = message.recurrence_days.split(',')
                                    current_day = message.send_time.strftime('%a').lower()
                                    days_cycle = days[days.index(current_day):] + days[:days.index(current_day)]
                                    
                                    for day in days_cycle[1:] + [days_cycle[0]]:
                                        next_time = message.send_time
                                        while next_time.strftime('%a').lower() != day:
                                            next_time += timedelta(days=1)
                                        if next_time > current_time:
                                            break
                                
                                if next_time:
                                    DatabaseManager.update_send_time(message.id, next_time)
                                else:
                                    DatabaseManager.mark_as_sent(message.id)
                            else:
                                DatabaseManager.mark_as_sent(message.id)
                            
                            # Se il messaggio è stato inviato con successo, esci dal ciclo di tentativi
                            break
                            
                        except Exception as e:
                            logger.error(f"Tentativo {attempt + 1}/{max_retries} fallito per il messaggio {message.id}: {e}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                            else:
                                logger.error(f"Messaggio {message.id} fallito dopo {max_retries} tentativi")

        except Exception as e:
            logger.error(f"Errore scheduler: {e}")

        await asyncio.sleep(60)

# Registrazione degli handler
async def register_handlers(dp: Dispatcher):
    # Handler comuni
    dp.message.register(cmd_start, CommandStart())
    dp.callback_query.register(return_to_main_menu, lambda c: c.data == "main_menu")
    
    # Handlers per messaggi immediati
    dp.callback_query.register(send_message_handler, lambda c: c.data == "send_message")
    dp.callback_query.register(group_selection_handler, lambda c: c.data.startswith("group_"))
    dp.callback_query.register(process_pin, lambda c: c.data.startswith("pin_"))
    dp.message.register(process_message, States.WAITING_MESSAGE)
    
    # Handlers per messaggi schedulati
    dp.callback_query.register(schedule_start_handler, lambda c: c.data == "schedule_message")
    dp.callback_query.register(schedule_group_handler, lambda c: c.data.startswith("schedule_to_"))
    dp.callback_query.register(schedule_type_handler, lambda c: c.data.startswith("schedule_type_"))
    dp.callback_query.register(schedule_days_handler, lambda c: c.data.startswith("day_") or c.data == "days_confirm")
    dp.message.register(process_schedule_time, States.SCHEDULE_WAITING_TIME)
    dp.message.register(process_scheduled_message, States.SCHEDULE_WAITING_MESSAGE)
    dp.callback_query.register(process_schedule_pin, lambda c: c.data.startswith("schedule_pin_"))
    
    # Handlers per lista messaggi
    dp.callback_query.register(list_messages_handler, lambda c: c.data == "list_messages")
    dp.callback_query.register(filter_messages_handler, lambda c: c.data.startswith("filter_"))
    dp.callback_query.register(view_message_details, lambda c: c.data == "view_message_details")
    dp.message.register(process_message_details, States.VIEWING_MESSAGE)
    dp.callback_query.register(toggle_message_handler, lambda c: c.data.startswith("toggle_"))
    dp.callback_query.register(delete_message_handler, lambda c: c.data.startswith("delete_"))
    dp.callback_query.register(confirm_delete_handler, lambda c: c.data.startswith("confirm_delete_") or c.data == "cancel_delete")

async def shutdown(loop, signal=None):
    """Gestione pulita dello shutdown."""
    if signal:
        logger.info(f"Ricevuto segnale di arresto: {signal.name}")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    [task.cancel() for task in tasks]
    logger.info(f"Cancellazione di {len(tasks)} task in corso")
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    
    if signal:
        loop.remove_signal_handler(signal.SIGTERM)
        loop.remove_signal_handler(signal.SIGINT)
    
    await bot.session.close()
    logger.info("Connessione del bot chiusa")

async def main():
    global bot, dp
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(loop, s))
        )
    
    logger.info("Avvio bot...")
    DatabaseManager.init_db()
    logger.info("Database inizializzato")
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    await register_handlers(dp)
    
    # Start bot and scheduler
    scheduler_task = asyncio.create_task(scheduler())
    
    try:
        logger.info(f"Bot avviato. Admin ID: {ADMIN_ID}")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        logger.info("Arresto del bot...")
        await shutdown(loop)

if __name__ == "__main__":
    try:
        # Imposta il loop degli eventi
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Avvia il bot
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Processo terminato dall'utente")
    finally:
        # Chiudi il loop degli eventi
        loop.close()
        logger.info("Loop degli eventi chiuso")