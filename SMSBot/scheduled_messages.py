import logging
from datetime import datetime, timedelta
import pytz
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from config import admin_id, gruppo_1_id, gruppo_2_id, gruppo_1_name, gruppo_2_name, bot_token
from keyboards import main_menu_keyboard

scheduled_router = Router()
logger = logging.getLogger(__name__)

# Dizionario per memorizzare i messaggi programmati
# Struttura: {message_id: {"chat_id": int, "text": str, "send_time": datetime, "pin": bool}}
scheduled_messages = {}

class ScheduleMessageStates(StatesGroup):
    selecting_group = State()
    entering_message = State()
    selecting_date = State()
    selecting_time = State()
    confirming = State()
    selecting_pin = State()

def scheduled_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Nuovo Messaggio Programmato", callback_data="schedule_new")],
        [InlineKeyboardButton(text="📋 Lista Messaggi Programmati", callback_data="schedule_list")],
        [InlineKeyboardButton(text="❌ Elimina Programmazione", callback_data="schedule_delete")],
        [InlineKeyboardButton(text="🔙 Menu Principale", callback_data="menu_back")]
    ])

def get_group_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👥 {gruppo_1_name}", callback_data=f"schedule_group_{gruppo_1_id}")],
        [InlineKeyboardButton(text=f"👥 {gruppo_2_name}", callback_data=f"schedule_group_{gruppo_2_id}")],
        [InlineKeyboardButton(text="🔙 Indietro", callback_data="schedule_back")]
    ])

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Conferma", callback_data="schedule_confirm"),
            InlineKeyboardButton(text="❌ Annulla", callback_data="schedule_cancel")
        ]
    ])

def get_pin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📌 Sì", callback_data="schedule_pin_yes"),
            InlineKeyboardButton(text="❌ No", callback_data="schedule_pin_no")
        ]
    ])

async def show_scheduled_menu(message: Message):
    """Mostra il menu dei messaggi programmati."""
    text = (
        "📅 <b>Gestione Messaggi Programmati</b>\n\n"
        "Qui puoi:\n"
        "• Programmare nuovi messaggi\n"
        "• Visualizzare i messaggi programmati\n"
        "• Eliminare programmazioni esistenti"
    )
    try:
        await message.edit_text(text, reply_markup=scheduled_menu_keyboard())
    except Exception:
        await message.answer(text, reply_markup=scheduled_menu_keyboard())

def format_scheduled_message(msg_id: str, msg_data: dict) -> str:
    """Formatta un messaggio programmato per la visualizzazione."""
    group_name = gruppo_1_name if msg_data["chat_id"] == gruppo_1_id else gruppo_2_name
    send_time = msg_data["send_time"].strftime("%d/%m/%Y %H:%M")
    pin_status = "📌" if msg_data.get("pin", False) else ""
    return (
        f"🔹 <b>Messaggio #{msg_id}</b> {pin_status}\n"
        f"📅 Data: {send_time}\n"
        f"👥 Gruppo: {group_name}\n"
        f"📝 Testo: {msg_data['text'][:100]}..."
    )

@scheduled_router.callback_query(lambda c: c.data == "schedule_new")
async def schedule_new_message(callback: CallbackQuery, state: FSMContext):
    """Inizia il processo di creazione di un nuovo messaggio programmato."""
    if callback.from_user.id != admin_id:
        await callback.answer("⛔ Non sei autorizzato", show_alert=True)
        return

    await state.set_state(ScheduleMessageStates.selecting_group)
    await callback.message.edit_text(
        "👥 <b>Seleziona il gruppo di destinazione:</b>",
        reply_markup=get_group_keyboard()
    )

@scheduled_router.callback_query(lambda c: c.data.startswith("schedule_group_"))
async def group_selected(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione del gruppo per il messaggio programmato."""
    chat_id = int(callback.data.split("schedule_group_")[1])
    await state.update_data(chat_id=chat_id)
    await state.set_state(ScheduleMessageStates.entering_message)
    
    await callback.message.edit_text(
        "📝 <b>Inserisci il messaggio da inviare:</b>\n\n"
        "<i>Puoi usare la formattazione HTML</i>"
    )

@scheduled_router.message(ScheduleMessageStates.entering_message)
async def message_entered(message: Message, state: FSMContext):
    """Gestisce l'inserimento del testo del messaggio."""
    await state.update_data(text=message.html_text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Oggi", callback_data="schedule_date_today")],
        [InlineKeyboardButton(text="📅 Domani", callback_data="schedule_date_tomorrow")],
        [InlineKeyboardButton(text="❌ Annulla", callback_data="schedule_cancel")]
    ])
    
    await message.answer(
        "📅 <b>Seleziona la data di invio:</b>",
        reply_markup=keyboard
    )
    await state.set_state(ScheduleMessageStates.selecting_date)

@scheduled_router.callback_query(lambda c: c.data.startswith("schedule_date_"))
async def date_selected(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione della data."""
    date_type = callback.data.split("schedule_date_")[1]
    now = datetime.now(pytz.UTC)
    
    if date_type == "today":
        selected_date = now.date()
    elif date_type == "tomorrow":
        selected_date = (now + timedelta(days=1)).date()
    else:
        await callback.answer("Data non valida", show_alert=True)
        return
    
    await state.update_data(date=selected_date)
    
    time_buttons = []
    current_time = now.replace(minute=0, second=0, microsecond=0)
    end_time = current_time + timedelta(days=1)
    
    while current_time < end_time:
        if current_time > now:
            time_str = current_time.strftime("%H:%M")
            time_buttons.append([
                InlineKeyboardButton(
                    text=time_str,
                    callback_data=f"schedule_time_{time_str}"
                )
            ])
        current_time += timedelta(minutes=30)
    
    time_buttons.append([InlineKeyboardButton(text="❌ Annulla", callback_data="schedule_cancel")])
    
    await callback.message.edit_text(
        "🕒 <b>Seleziona l'orario di invio:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=time_buttons)
    )
    await state.set_state(ScheduleMessageStates.selecting_time)

@scheduled_router.callback_query(lambda c: c.data.startswith("schedule_time_"))
async def time_selected(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione dell'orario."""
    time_str = callback.data.split("schedule_time_")[1]
    data = await state.get_data()
    
    hour, minute = map(int, time_str.split(":"))
    send_time = datetime.combine(data["date"], datetime.min.time().replace(hour=hour, minute=minute))
    send_time = pytz.UTC.localize(send_time)
    
    await state.update_data(send_time=send_time)
    
    await callback.message.edit_text(
        "📌 <b>Vuoi pinnare il messaggio quando verrà inviato?</b>",
        reply_markup=get_pin_keyboard()
    )
    await state.set_state(ScheduleMessageStates.selecting_pin)

@scheduled_router.callback_query(lambda c: c.data.startswith("schedule_pin_"))
async def pin_selected(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione del pin."""
    pin = callback.data == "schedule_pin_yes"
    data = await state.get_data()
    await state.update_data(pin=pin)
    
    group_name = gruppo_1_name if data["chat_id"] == gruppo_1_id else gruppo_2_name
    send_time = data["send_time"].strftime("%d/%m/%Y %H:%M")
    
    await callback.message.edit_text(
        "📋 <b>Riepilogo Programmazione:</b>\n\n"
        f"👥 Gruppo: {group_name}\n"
        f"📅 Data e ora: {send_time}\n"
        f"📌 Pin: {'Sì' if pin else 'No'}\n"
        f"📝 Messaggio:\n\n"
        f"{data['text']}\n\n"
        "Confermi la programmazione?",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(ScheduleMessageStates.confirming)

@scheduled_router.callback_query(lambda c: c.data == "schedule_confirm")
async def confirm_schedule(callback: CallbackQuery, state: FSMContext):
    """Gestisce la conferma della programmazione."""
    data = await state.get_data()
    
    message_id = str(len(scheduled_messages) + 1)
    
    scheduled_messages[message_id] = {
        "chat_id": data["chat_id"],
        "text": data["text"],
        "send_time": data["send_time"],
        "pin": data.get("pin", False)
    }
    
    await callback.message.edit_text(
        "✅ <b>Messaggio programmato con successo!</b>\n\n"
        "Usa /scheduled per vedere la lista dei messaggi programmati.",
        reply_markup=scheduled_menu_keyboard()
    )
    logger.info(f"Nuovo messaggio programmato: #{message_id} per il {data['send_time']}")
    await state.clear()

@scheduled_router.callback_query(lambda c: c.data == "schedule_list")
async def list_scheduled_messages(callback: CallbackQuery):
    """Mostra la lista dei messaggi programmati."""
    if not scheduled_messages:
        await callback.message.edit_text(
            "📝 <b>Nessun messaggio programmato</b>",
            reply_markup=scheduled_menu_keyboard()
        )
        return
    
    text = "📋 <b>Messaggi Programmati:</b>\n\n"
    for msg_id, msg_data in sorted(
        scheduled_messages.items(),
        key=lambda x: x[1]["send_time"]
    ):
        text += format_scheduled_message(msg_id, msg_data) + "\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=scheduled_menu_keyboard()
    )

@scheduled_router.callback_query(lambda c: c.data == "schedule_delete")
async def delete_schedule_menu(callback: CallbackQuery):
    """Mostra il menu per eliminare i messaggi programmati."""
    if not scheduled_messages:
        await callback.answer("Non ci sono messaggi programmati da eliminare", show_alert=True)
        return
    
    keyboard = []
    for msg_id, msg_data in sorted(
        scheduled_messages.items(),
        key=lambda x: x[1]["send_time"]
    ):
        send_time = msg_data["send_time"].strftime("%d/%m/%Y %H:%M")
        group_name = gruppo_1_name if msg_data["chat_id"] == gruppo_1_id else gruppo_2_name
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {send_time} - {group_name}",
                callback_data=f"schedule_delete_{msg_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Indietro", callback_data="schedule_back")])
    
    await callback.message.edit_text(
        "❌ <b>Seleziona il messaggio da eliminare:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@scheduled_router.callback_query(lambda c: c.data.startswith("schedule_delete_"))
async def delete_scheduled_message(callback: CallbackQuery):
    """Elimina un messaggio programmato."""
    msg_id = callback.data.split("schedule_delete_")[1]
    if msg_id in scheduled_messages:
        del scheduled_messages[msg_id]
        await callback.answer("✅ Messaggio eliminato!", show_alert=True)
        logger.info(f"Messaggio programmato #{msg_id} eliminato")
    else:
        await callback.answer("❌ Messaggio non trovato!", show_alert=True)
    
    await show_scheduled_menu(callback.message)

@scheduled_router.callback_query(lambda c: c.data == "schedule_back")
async def back_to_schedule_menu(callback: CallbackQuery, state: FSMContext):
    """Torna al menu dei messaggi programmati."""
    await state.clear()
    await show_scheduled_menu(callback.message)

@scheduled_router.callback_query(lambda c: c.data == "schedule_cancel")
async def cancel_scheduling(callback: CallbackQuery, state: FSMContext):
    """Annulla la programmazione corrente."""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Operazione annullata</b>",
        reply_markup=scheduled_menu_keyboard()
    )

@scheduled_router.callback_query(lambda c: c.data == "menu_back")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Torna al menu principale."""
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Menu Principale</b>\n\n"
        "Seleziona un'opzione:",
        reply_markup=main_menu_keyboard()
    )

@scheduled_router.message(Command("scheduled"))
async def cmd_scheduled(message: Message):
    """Gestisce il comando /scheduled."""
    if message.from_user.id != admin_id:
        await message.answer("⛔ Non sei autorizzato")
        return
        
    if not scheduled_messages:
        await message.answer(
            "📝 <b>Nessun messaggio programmato</b>",
            reply_markup=scheduled_menu_keyboard()
        )
        return
    
    text = "📋 <b>Messaggi Programmati:</b>\n\n"
    for msg_id, msg_data in sorted(
        scheduled_messages.items(),
        key=lambda x: x[1]["send_time"]
    ):
        text += format_scheduled_message(msg_id, msg_data) + "\n\n"
    
    await message.answer(text, reply_markup=scheduled_menu_keyboard())

async def send_scheduled_messages():
    """Invia i messaggi programmati quando è il momento."""
    now = datetime.now(pytz.UTC)
    messages_to_remove = []
    
    for msg_id, msg_data in scheduled_messages.items():
        if msg_data["send_time"] <= now:
            try:
                sent_msg = await bot.send_message(
                    chat_id=msg_data["chat_id"],
                    text=msg_data["text"]
                )
                
                if msg_data.get("pin", False):
                    await bot.pin_chat_message(
                        chat_id=msg_data["chat_id"],
                        message_id=sent_msg.message_id
                    )
                
                logger.info(f"Messaggio programmato #{msg_id} inviato con successo")
                messages_to_remove.append(msg_id)
                
            except Exception as e:
                logger.error(f"Errore nell'invio del messaggio programmato #{msg_id}: {e}")
    
    for msg_id in messages_to_remove:
        del scheduled_messages[msg_id]