from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Restituisce la tastiera principale."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Invia Messaggio")],
            [KeyboardButton(text="⏰ Messaggi Programmati")],
            [KeyboardButton(text="ℹ️ Info")]
        ],
        resize_keyboard=True
    )

def get_group_keyboard() -> ReplyKeyboardMarkup:
    """Restituisce la tastiera per la selezione del gruppo."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Gruppo Clienti"),
                KeyboardButton(text="👥 Gruppo Reseller")
            ],
            [KeyboardButton(text="👥 Entrambi i Gruppi")],  # Nuovo pulsante
            [KeyboardButton(text="❌ Annulla")]
        ],
        resize_keyboard=True
    )

def get_schedule_keyboard() -> ReplyKeyboardMarkup:
    """Restituisce la tastiera per la scelta dell'invio."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📤 Invia Ora"),
                KeyboardButton(text="⏰ Programma")
            ],
            [KeyboardButton(text="❌ Annulla")]
        ],
        resize_keyboard=True
    )