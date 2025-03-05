from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from database.models import RecurrenceType

def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per la programmazione dei messaggi."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📨 Invia Ora', callback_data='send_now')],
            [InlineKeyboardButton(text='⏰ Programma', callback_data='schedule')],
            [InlineKeyboardButton(text='❌ Annulla', callback_data='cancel')]
        ]
    )
    return keyboard

def get_pin_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per scegliere se pinnare il messaggio."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='📌 Pinna', callback_data='pin_yes'),
                InlineKeyboardButton(text='No Pin', callback_data='pin_no')
            ]
        ]
    )
    return keyboard

def get_recurrence_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per la selezione del tipo di ricorrenza."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Nessuna ricorrenza", callback_data="recurrence_none")],
            [InlineKeyboardButton(text="📅 Ogni giorno", callback_data="recurrence_daily")],
            [InlineKeyboardButton(text="📆 Settimanale", callback_data="recurrence_weekly")]
        ]
    )
    return keyboard

def get_days_keyboard(selected_days: list = None) -> InlineKeyboardMarkup:
    """Tastiera per la selezione dei giorni della settimana."""
    if selected_days is None:
        selected_days = []
    
    days = [
        ("Lun", "1"), ("Mar", "2"), ("Mer", "3"),
        ("Gio", "4"), ("Ven", "5"), ("Sab", "6"),
        ("Dom", "7")
    ]
    
    # Crea i pulsanti dei giorni in gruppi di 3
    buttons = []
    current_row = []
    for day_name, day_num in days:
        if day_num in selected_days:
            day_name = f"✅ {day_name}"
        current_row.append(InlineKeyboardButton(
            text=day_name,
            callback_data=f"day_{day_num}"
        ))
        if len(current_row) == 3:
            buttons.append(current_row)
            current_row = []
    
    if current_row:  # Aggiungi eventuali pulsanti rimanenti
        buttons.append(current_row)
    
    # Aggiungi i pulsanti di conferma e annulla
    buttons.append([InlineKeyboardButton(text="✅ Conferma", callback_data="days_confirm")])
    buttons.append([InlineKeyboardButton(text="❌ Annulla", callback_data="cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_scheduled_messages_keyboard(messages) -> InlineKeyboardMarkup:
    """Tastiera per gestire i messaggi programmati."""
    buttons = []
    
    for msg in messages:
        # Formatta la data in modo leggibile
        send_time = msg.send_time.strftime("%d/%m/%Y %H:%M")
        
        # Crea il testo del pulsante
        recurrence_text = ""
        if msg.recurrence_type == RecurrenceType.DAILY:
            recurrence_text = " [Ogni giorno]"
        elif msg.recurrence_type == RecurrenceType.WEEKLY:
            days = sorted(msg.recurrence_days.split(','))
            days_text = ','.join([['L','M','M','G','V','S','D'][int(d)-1] for d in days])
            recurrence_text = f" [{days_text}]"
            
        button_text = f"🕐 {send_time}{recurrence_text}"
        if msg.pin:
            button_text += " 📌"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f'view_msg_{msg.id}'
        )])
    
    if len(messages) > 0:
        buttons.append([InlineKeyboardButton(text='❌ Elimina Tutti', callback_data='delete_all')])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_message_management_keyboard(message_id: int) -> InlineKeyboardMarkup:
    """Tastiera per gestire un singolo messaggio programmato."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='❌ Elimina', callback_data=f'delete_msg_{message_id}'),
                InlineKeyboardButton(text='🔙 Indietro', callback_data='back_to_scheduled')
            ]
        ]
    )
    return keyboard