import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import admin_id, gruppo_1_id, gruppo_2_id, gruppo_1_name, gruppo_2_name
from keyboards import messages_menu_keyboard, confirm_send_keyboard, pin_keyboard, main_menu_keyboard

messages_router = Router()
logger = logging.getLogger(__name__)

class MessageStates(StatesGroup):
    waiting_for_message = State()
    confirming = State()
    selecting_pin = State()

async def show_messages_menu(message: Message):
    """Mostra il menu principale dei messaggi."""
    text = (
        "📨 <b>Gestione Messaggi</b>\n\n"
        "Seleziona il gruppo a cui inviare il messaggio:"
    )
    try:
        await message.edit_text(text, reply_markup=messages_menu_keyboard())
    except Exception:
        await message.answer(text, reply_markup=messages_menu_keyboard())

@messages_router.callback_query(lambda c: c.data == "menu_messages")
async def process_messages_menu(callback: CallbackQuery):
    """Gestisce il click sul pulsante del menu messaggi."""
    if callback.from_user.id != admin_id:
        await callback.answer("⛔ Non sei autorizzato", show_alert=True)
        return
    await show_messages_menu(callback.message)
    await callback.answer()

@messages_router.callback_query(lambda c: c.data.startswith("send_group_"))
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione del gruppo."""
    if callback.from_user.id != admin_id:
        await callback.answer("⛔ Non sei autorizzato", show_alert=True)
        return

    group_num = callback.data.split("_")[-1]
    chat_id = gruppo_1_id if group_num == "1" else gruppo_2_id
    group_name = gruppo_1_name if group_num == "1" else gruppo_2_name
    
    await state.update_data(selected_chat_id=chat_id, group_name=group_name)
    await state.set_state(MessageStates.waiting_for_message)
    
    await callback.message.edit_text(
        f"📝 <b>Invia il messaggio per {group_name}</b>\n\n"
        "<i>Puoi usare la formattazione HTML nel testo</i>"
    )
    await callback.answer()

@messages_router.message(MessageStates.waiting_for_message)
async def process_message(message: Message, state: FSMContext):
    """Gestisce il messaggio ricevuto dall'utente."""
    if message.from_user.id != admin_id:
        return

    await state.update_data(message_text=message.html_text)
    data = await state.get_data()
    
    await message.answer(
        "📌 <b>Vuoi pinnare questo messaggio?</b>",
        reply_markup=pin_keyboard()
    )
    await state.set_state(MessageStates.selecting_pin)

@messages_router.callback_query(lambda c: c.data.startswith("pin_"))
async def process_pin_selection(callback: CallbackQuery, state: FSMContext):
    """Gestisce la selezione del pin."""
    if callback.from_user.id != admin_id:
        await callback.answer("⛔ Non sei autorizzato", show_alert=True)
        return

    pin = callback.data == "pin_yes"
    await state.update_data(pin_message=pin)
    data = await state.get_data()
    
    group_name = data['group_name']
    message_text = data['message_text']
    
    confirmation_text = (
        f"📋 <b>Conferma invio:</b>\n\n"
        f"👥 Gruppo: {group_name}\n"
        f"📌 Pin: {'Sì' if pin else 'No'}\n\n"
        f"📝 Messaggio:\n\n"
        f"{message_text}"
    )
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=confirm_send_keyboard()
    )
    await state.set_state(MessageStates.confirming)

@messages_router.callback_query(lambda c: c.data == "confirm_send")
async def process_send_confirmation(callback: CallbackQuery, state: FSMContext):
    """Gestisce la conferma dell'invio del messaggio."""
    if callback.from_user.id != admin_id:
        await callback.answer("⛔ Non sei autorizzato", show_alert=True)
        return

    data = await state.get_data()
    try:
        sent_message = await callback.bot.send_message(
            chat_id=data['selected_chat_id'],
            text=data['message_text']
        )
        
        if data.get('pin_message', False):
            await callback.bot.pin_chat_message(
                chat_id=data['selected_chat_id'],
                message_id=sent_message.message_id
            )
        
        await callback.message.edit_text(
            "✅ <b>Messaggio inviato con successo!</b>",
            reply_markup=messages_menu_keyboard()
        )
        logger.info(f"Messaggio inviato con successo al gruppo {data['group_name']}")
        
    except Exception as e:
        logger.error(f"Errore nell'invio del messaggio: {e}")
        await callback.message.edit_text(
            "❌ <b>Errore nell'invio del messaggio</b>\n\n"
            "Riprova più tardi.",
            reply_markup=messages_menu_keyboard()
        )
    
    await state.clear()
    await callback.answer()

@messages_router.callback_query(lambda c: c.data == "cancel_send")
async def process_send_cancellation(callback: CallbackQuery, state: FSMContext):
    """Gestisce l'annullamento dell'invio."""
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Invio annullato</b>",
        reply_markup=messages_menu_keyboard()
    )
    await callback.answer()

@messages_router.callback_query(lambda c: c.data == "menu_back")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Torna al menu principale."""
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Menu Principale</b>\n\n"
        "Seleziona un'opzione:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()