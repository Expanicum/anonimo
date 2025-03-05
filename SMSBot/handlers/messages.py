import calendar
from datetime import datetime, timedelta
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config.config import config
from database.database import DatabaseManager
from database.models import RecurrenceType, MessageType
from keyboards.base import get_main_keyboard, get_group_keyboard, get_schedule_keyboard
from utils.states import BotStates

router = Router()

@router.message(F.text == "📝 Invia Messaggio")
async def cmd_send_message(message: types.Message, state: FSMContext):
    """Gestisce il comando per inviare un messaggio."""
    if message.from_user.id != config.admin_id:
        return
        
    await message.reply(
        "👥 Seleziona il gruppo a cui inviare il messaggio:",
        reply_markup=get_group_keyboard()
    )
    await state.set_state(BotStates.waiting_for_group)

@router.message(BotStates.waiting_for_group)
async def process_group_selection(message: types.Message, state: FSMContext):
    """Gestisce la selezione del gruppo."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return
        
    if message.text == "👥 Gruppo Clienti":
        chat_ids = [config.gruppo_clienti_id]
        chat_names = [config.gruppo_clienti_name]
    elif message.text == "👥 Gruppo Reseller":
        chat_ids = [config.gruppo_reseller_id]
        chat_names = [config.gruppo_reseller_name]
    elif message.text == "👥 Entrambi i Gruppi":
        chat_ids = [config.gruppo_clienti_id, config.gruppo_reseller_id]
        chat_names = [config.gruppo_clienti_name, config.gruppo_reseller_name]
    else:
        await message.reply("❌ Selezione non valida. Usa la tastiera.")
        return
        
    await state.update_data(chat_ids=chat_ids, chat_names=chat_names)
    await message.reply(
        f"📝 Inviami il messaggio da inviare a: {', '.join(chat_names)}.\n"
        "Puoi inviare testo, foto, video, documenti, audio o messaggi vocali.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Annulla")]],
            resize_keyboard=True
        )
    )
    await state.set_state(BotStates.waiting_for_message)

@router.message(BotStates.waiting_for_message)
async def process_message(message: types.Message, state: FSMContext):
    """Gestisce il messaggio ricevuto dall'utente."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    message_type = None
    text = None
    file_id = None
    caption = None

    # Determina il tipo di messaggio e estrai le informazioni rilevanti
    if message.text:
        message_type = MessageType.TEXT
        text = message.text
    elif message.photo:
        message_type = MessageType.PHOTO
        file_id = message.photo[-1].file_id
        caption = message.caption
    elif message.video:
        message_type = MessageType.VIDEO
        file_id = message.video.file_id
        caption = message.caption
    elif message.document:
        message_type = MessageType.DOCUMENT
        file_id = message.document.file_id
        caption = message.caption
    elif message.audio:
        message_type = MessageType.AUDIO
        file_id = message.audio.file_id
        caption = message.caption
    elif message.voice:
        message_type = MessageType.VOICE
        file_id = message.voice.file_id
        caption = message.caption
    elif message.animation:
        message_type = MessageType.ANIMATION
        file_id = message.animation.file_id
        caption = message.caption
    else:
        await message.reply("❌ Tipo di messaggio non supportato!")
        return

    # Salva le informazioni nello state
    await state.update_data(
        message_type=message_type,
        text=text,
        file_id=file_id,
        caption=caption
    )
    
    await message.reply(
        "⏰ Vuoi inviare il messaggio ora o programmarlo per dopo?",
        reply_markup=get_schedule_keyboard()
    )
    await state.set_state(BotStates.waiting_for_schedule)

@router.message(BotStates.waiting_for_schedule)
async def process_schedule_choice(message: types.Message, state: FSMContext):
    """Gestisce la scelta di schedulazione."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    if message.text == "📤 Invia Ora":
        # Prima chiediamo se pinnare il messaggio
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📌 Sì"),
                    KeyboardButton(text="❌ No")
                ],
                [KeyboardButton(text="❌ Annulla")]
            ],
            resize_keyboard=True
        )
        
        await message.reply(
            "📌 Vuoi che il messaggio venga pinnato?",
            reply_markup=keyboard
        )
        await state.update_data(immediate_send=True)
        await state.set_state(BotStates.waiting_for_pin)
        
    elif message.text == "⏰ Programma":
        # Chiedi la data
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📅 Oggi"),
                    KeyboardButton(text="📅 Domani")
                ],
                [KeyboardButton(text="❌ Annulla")]
            ],
            resize_keyboard=True
        )
        
        await message.reply(
            "📅 Seleziona la data per l'invio del messaggio:\n"
            "Puoi usare i pulsanti rapidi o inviare una data nel formato YYYY-MM-DD",
            reply_markup=keyboard
        )
        await state.set_state(BotStates.waiting_for_date)
    else:
        await message.reply("❌ Selezione non valida. Usa la tastiera.")

@router.message(BotStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    """Gestisce l'input della data."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        if message.text == "📅 Oggi":
            selected_date = datetime.utcnow().date()
        elif message.text == "📅 Domani":
            selected_date = (datetime.utcnow() + timedelta(days=1)).date()
        else:
            selected_date = datetime.strptime(message.text, "%Y-%m-%d").date()
            
        # Verifica che la data non sia nel passato
        if selected_date < datetime.utcnow().date():
            await message.reply("❌ Non puoi selezionare una data nel passato!")
            return
            
        await state.update_data(selected_date=selected_date)
        
        # Chiedi l'ora
        await message.reply(
            "🕒 Inserisci l'ora per l'invio del messaggio (formato HH:MM):",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="❌ Annulla")]],
                resize_keyboard=True
            )
        )
        await state.set_state(BotStates.waiting_for_time)
        
    except ValueError:
        await message.reply(
            "❌ Formato data non valido. Usa YYYY-MM-DD o i pulsanti rapidi."
        )

@router.message(BotStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    """Gestisce l'input dell'ora."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        # Parsing dell'ora
        hour, minute = map(int, message.text.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
            
        data = await state.get_data()
        selected_date = data['selected_date']
        
        # Crea il datetime completo
        send_time = datetime.combine(
            selected_date,
            datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
        )
        
        # Verifica che l'orario non sia nel passato
        if send_time <= datetime.utcnow():
            await message.reply("❌ Non puoi selezionare un orario nel passato!")
            return
            
        await state.update_data(send_time=send_time)
        
        # Chiedi se il messaggio deve essere ricorrente
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🔄 Ogni Giorno"),
                    KeyboardButton(text="🔄 Ogni Settimana")
                ],
                [KeyboardButton(text="❌ No")],
                [KeyboardButton(text="❌ Annulla")]
            ],
            resize_keyboard=True
        )
        
        await message.reply(
            "🔄 Vuoi che il messaggio sia ricorrente?",
            reply_markup=keyboard
        )
        await state.set_state(BotStates.waiting_for_recurrence)
        
    except (ValueError, IndexError):
        await message.reply("❌ Formato ora non valido. Usa HH:MM")

@router.message(BotStates.waiting_for_recurrence)
async def process_recurrence(message: types.Message, state: FSMContext):
    """Gestisce la scelta della ricorrenza."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    if message.text == "🔄 Ogni Giorno":
        await state.update_data(recurrence_type=RecurrenceType.DAILY)
        await process_pin_choice(message, state)
        
    elif message.text == "🔄 Ogni Settimana":
        await state.update_data(recurrence_type=RecurrenceType.WEEKLY)
        
        # Chiedi i giorni della settimana
        keyboard = []
        days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        # Crea una griglia 2x4 di pulsanti
        for i in range(0, len(days), 2):
            row = []
            for j in range(2):
                if i + j < len(days):
                    row.append(KeyboardButton(text=days[i + j]))
            keyboard.append(row)
            
        keyboard.append([KeyboardButton(text="✅ Fatto")])
        keyboard.append([KeyboardButton(text="❌ Annulla")])
        
        await message.reply(
            "📅 Seleziona i giorni della settimana in cui inviare il messaggio.\n"
            "Premi ✅ Fatto quando hai finito.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True
            )
        )
        await state.update_data(selected_days=[])
        await state.set_state(BotStates.waiting_for_days)
        
    elif message.text == "❌ No":
        await state.update_data(recurrence_type=RecurrenceType.NONE)
        await process_pin_choice(message, state)
        
    else:
        await message.reply("❌ Selezione non valida. Usa la tastiera.")

@router.message(BotStates.waiting_for_days)
async def process_days(message: types.Message, state: FSMContext):
    """Gestisce la selezione dei giorni per la ricorrenza settimanale."""
    if message.text == "✅ Fatto":
        data = await state.get_data()
        selected_days = data.get('selected_days', [])
        
        if not selected_days:
            await message.reply("❌ Devi selezionare almeno un giorno!")
            return
            
        # Converti i nomi dei giorni in numeri (1-7)
        day_map = {
            "Lunedì": 1, "Martedì": 2, "Mercoledì": 3, "Giovedì": 4,
            "Venerdì": 5, "Sabato": 6, "Domenica": 7
        }
        
        days_numbers = [str(day_map[day]) for day in selected_days]
        await state.update_data(recurrence_days=','.join(days_numbers))
        
        await process_pin_choice(message, state)
        
    elif message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        
    else:
        # Aggiungi o rimuovi il giorno dalla lista
        data = await state.get_data()
        selected_days = data.get('selected_days', [])
        
        if message.text in ["Lunedì", "Martedì", "Mercoledì", "Giovedì", 
                           "Venerdì", "Sabato", "Domenica"]:
            if message.text in selected_days:
                selected_days.remove(message.text)
                await message.reply(f"❌ Rimosso {message.text}")
            else:
                selected_days.append(message.text)
                await message.reply(f"✅ Aggiunto {message.text}")
                
            await state.update_data(selected_days=selected_days)
            
        else:
            await message.reply("❌ Selezione non valida. Usa la tastiera.")

async def process_pin_choice(message: types.Message, state: FSMContext):
    """Chiede se il messaggio deve essere pinnato."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📌 Sì"),
                KeyboardButton(text="❌ No")
            ],
            [KeyboardButton(text="❌ Annulla")]
        ],
        resize_keyboard=True
    )
    
    await message.reply(
        "📌 Vuoi che il messaggio venga pinnato dopo l'invio?",
        reply_markup=keyboard
    )
    await state.set_state(BotStates.waiting_for_pin)

@router.message(BotStates.waiting_for_pin)
async def process_pin(message: types.Message, state: FSMContext):
    """Gestisce la scelta del pin e finalizza la programmazione."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    if message.text not in ["📌 Sì", "❌ No"]:
        await message.reply("❌ Selezione non valida. Usa la tastiera.")
        return
        
    pin = message.text == "📌 Sì"
    data = await state.get_data()
    
    try:
        scheduled_messages = []
        for chat_id in data['chat_ids']:
            send_time = data.get('send_time', datetime.utcnow())
            
            # Aggiungi il messaggio al database per ogni gruppo
            scheduled_message = DatabaseManager.add_scheduled_message(
                chat_id=chat_id,
                send_time=send_time,
                message_type=data['message_type'],
                text=data.get('text'),
                file_id=data.get('file_id'),
                caption=data.get('caption'),
                pin=pin,
                recurrence_type=data.get('recurrence_type', RecurrenceType.NONE),
                recurrence_days=data.get('recurrence_days')
            )
            scheduled_messages.append(scheduled_message)
        
        # Formatta il messaggio di conferma
        chat_names = data['chat_names']
        groups_text = f"👥 Gruppi: {', '.join(chat_names)}\n"
        
        # Anteprima del contenuto
        content_preview = ""
        if data.get('text'):
            content_preview = f"\n💬 Anteprima: {data['text'][:100]}{'...' if len(data['text']) > 100 else ''}"
        elif data.get('caption'):
            content_preview = f"\n💬 Didascalia: {data['caption'][:100]}{'...' if len(data['caption']) > 100 else ''}"
        
        recurrence_text = ""
        if data.get('recurrence_type') == RecurrenceType.DAILY:
            recurrence_text = "🔄 Il messaggio verrà inviato ogni giorno"
        elif data.get('recurrence_type') == RecurrenceType.WEEKLY:
            days = data.get('recurrence_days', '').split(',')
            day_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            selected_days = [day_names[int(d)-1] for d in days]
            recurrence_text = f"🔄 Il messaggio verrà inviato ogni settimana il: {', '.join(selected_days)}"
        
        if data.get('immediate_send'):
            await message.reply(
                f"✅ Messaggio inviato con successo!\n\n"
                f"{groups_text}"
                f"📌 Pin: {'Sì' if pin else 'No'}"
                f"{content_preview}",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.reply(
                f"✅ Messaggio programmato con successo!\n\n"
                f"{groups_text}"
                f"📅 Data: {scheduled_messages[0].send_time.strftime('%Y-%m-%d')}\n"
                f"🕒 Ora: {scheduled_messages[0].send_time.strftime('%H:%M')}\n"
                f"📌 Pin: {'Sì' if pin else 'No'}\n"
                f"{recurrence_text}"
                f"{content_preview}",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        await message.reply(
            f"❌ Errore durante la programmazione del messaggio: {e}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

@router.message(F.text == "⏰ Messaggi Programmati")
async def list_scheduled_messages(message: types.Message):
    """Lista tutti i messaggi programmati."""
    if message.from_user.id != config.admin_id:
        return
        
    messages = DatabaseManager.get_all_scheduled_messages()
    
    if not messages:
        await message.reply(
            "📭 Non ci sono messaggi programmati.",
            reply_markup=get_main_keyboard()
        )
        return
        
    response = "📋 Messaggi programmati:\n\n"
    
    for msg in messages:
        # Determina il tipo di contenuto
        content_type = {
            MessageType.TEXT: "📝 Testo",
            MessageType.PHOTO: "📷 Foto",
            MessageType.VIDEO: "🎥 Video",
            MessageType.DOCUMENT: "📎 Documento",
            MessageType.AUDIO: "🎵 Audio",
            MessageType.VOICE: "🎤 Messaggio vocale",
            MessageType.ANIMATION: "🎞 GIF"
        }.get(msg.message_type, "❓ Sconosciuto")
        
        # Determina il gruppo di destinazione
        chat_name = (
            config.gruppo_clienti_name if msg.chat_id == config.gruppo_clienti_id
            else config.gruppo_reseller_name if msg.chat_id == config.gruppo_reseller_id
            else "Gruppo sconosciuto"
        )
        
        # Anteprima del contenuto
        content_preview = ""
        if msg.text:
            content_preview = f"\n💬 Anteprima: {msg.text[:100]}{'...' if len(msg.text) > 100 else ''}"
        elif msg.caption:
            content_preview = f"\n💬 Didascalia: {msg.caption[:100]}{'...' if len(msg.caption) > 100 else ''}"
        
        # Formatta il testo della ricorrenza
        recurrence_text = ""
        if msg.recurrence_type == RecurrenceType.DAILY:
            recurrence_text = "🔄 Ogni giorno"
        elif msg.recurrence_type == RecurrenceType.WEEKLY:
            days = msg.recurrence_days.split(',')
            day_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            selected_days = [day_names[int(d)-1] for d in days]
            recurrence_text = f"🔄 Ogni settimana il: {', '.join(selected_days)}"
        
        # Stato attivo/inattivo
        active_status = "✅ Attivo" if msg.active else "❌ Disattivato"
        
        response += (
            f"ID: {msg.id}\n"
            f"👥 Gruppo: {chat_name}\n"
            f"📅 Data: {msg.send_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"📌 Pin: {'Sì' if msg.pin else 'No'}\n"
            f"📎 Tipo: {content_type}\n"
            f"🔄 Stato: {active_status}\n"
            f"{recurrence_text}"
            f"{content_preview}\n\n"
        )
    
    # Aggiungi pulsanti per gestire i messaggi
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Attiva/Disattiva Messaggio")],
            [KeyboardButton(text="🏠 Menu Principale")]
        ],
        resize_keyboard=True
    )
    
    await message.reply(response, reply_markup=keyboard)

@router.message(F.text == "🔄 Attiva/Disattiva Messaggio")
async def toggle_message_state(message: types.Message, state: FSMContext):
    """Gestisce l'attivazione/disattivazione di un messaggio."""
    await message.reply(
        "📝 Inserisci l'ID del messaggio da attivare/disattivare:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Annulla")]],
            resize_keyboard=True
        )
    )
    await state.set_state(BotStates.waiting_for_message_id)

@router.message(BotStates.waiting_for_message_id)
async def process_toggle_message(message: types.Message, state: FSMContext):
    """Processa l'ID del messaggio da attivare/disattivare."""
    if message.text == "❌ Annulla":
        await state.clear()
        await message.reply(
            "❌ Operazione annullata.",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        message_id = int(message.text)
        if DatabaseManager.toggle_message_active(message_id):
            await message.reply(
                "✅ Stato del messaggio modificato con successo!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.reply(
                "❌ Messaggio non trovato.",
                reply_markup=get_main_keyboard()
            )
    except ValueError:
        await message.reply(
            "❌ ID messaggio non valido. Deve essere un numero.",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "🏠 Menu Principale")
async def return_to_main_menu(message: types.Message):
    """Ritorna al menu principale."""
    await message.reply(
        "🏠 Menu Principale",
        reply_markup=get_main_keyboard()
    )

def register_message_handlers(dp: Router):
    """Registra gli handler dei messaggi."""
    dp.include_router(router)