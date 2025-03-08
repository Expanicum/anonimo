import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Prendi i nomi dei gruppi dalle variabili d'ambiente con valori di default
GRUPPO_1_NAME = os.getenv('GRUPPO_1_NAME', 'Clienti')
GRUPPO_2_NAME = os.getenv('GRUPPO_2_NAME', 'Reseller')

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Crea la tastiera del menu principale."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Invia Messaggio",
                callback_data="send_message"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Programma Messaggio",
                callback_data="schedule_message"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Lista Messaggi",
                callback_data="list_messages"
            )
        ]
    ])
    return keyboard

def groups_keyboard() -> InlineKeyboardMarkup:
    """Crea la tastiera per la selezione dei gruppi."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📢 {GRUPPO_1_NAME}",  # Usa il nome del gruppo
                callback_data="group_1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📢 {GRUPPO_2_NAME}",  # Usa il nome del gruppo
                callback_data="group_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Entrambi i gruppi",
                callback_data="group_both"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Torna al Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def schedule_groups_keyboard() -> InlineKeyboardMarkup:
    """Tastiera dedicata per la selezione gruppi in modalità scheduling."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📅 {GRUPPO_1_NAME}",
                callback_data="schedule_to_1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📅 {GRUPPO_2_NAME}",
                callback_data="schedule_to_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Entrambi i gruppi",
                callback_data="schedule_to_both"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Torna al Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def schedule_type_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per scegliere il tipo di schedulazione."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🕐 Una volta",
                callback_data="schedule_type_once"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Ogni giorno",
                callback_data="schedule_type_daily"
            )
        ],
        [
            InlineKeyboardButton(
                text="📆 Giorni specifici",
                callback_data="schedule_type_weekly"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def weekdays_keyboard(selected_days: list = None) -> InlineKeyboardMarkup:
    """Tastiera per selezionare i giorni della settimana."""
    if selected_days is None:
        selected_days = []
    
    days = {
        "mon": "Lunedì",
        "tue": "Martedì",
        "wed": "Mercoledì",
        "thu": "Giovedì",
        "fri": "Venerdì",
        "sat": "Sabato",
        "sun": "Domenica"
    }
    
    keyboard = []
    for day_code, day_name in days.items():
        selected = "✅" if day_code in selected_days else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{day_name} {selected}",
                callback_data=f"day_{day_code}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="✅ Conferma",
            callback_data="days_confirm"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Menu",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def pin_keyboard() -> InlineKeyboardMarkup:
    """Crea la tastiera per la scelta del pin."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Si",
                callback_data="pin_yes"
            ),
            InlineKeyboardButton(
                text="No",
                callback_data="pin_no"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def schedule_pin_keyboard() -> InlineKeyboardMarkup:
    """Tastiera dedicata per il pin dei messaggi schedulati."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Si",
                callback_data="schedule_pin_yes"
            ),
            InlineKeyboardButton(
                text="No",
                callback_data="schedule_pin_no"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def messages_filter_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per filtrare i messaggi per gruppo."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📢 {GRUPPO_1_NAME}",
                callback_data="filter_group1"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📢 {GRUPPO_2_NAME}",
                callback_data="filter_group2"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Tutti i gruppi",
                callback_data="filter_all"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def message_details_keyboard() -> InlineKeyboardMarkup:
    """Tastiera per le azioni disponibili nella vista dettagli."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔍 Visualizza Dettagli",
                callback_data="view_message_details"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Aggiorna Lista",
                callback_data="list_messages"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Menu",
                callback_data="main_menu"
            )
        ]
    ])
    return keyboard

def message_actions_keyboard(message_id: int = None) -> InlineKeyboardMarkup:
    """Crea la tastiera per le azioni sui messaggi programmati."""
    if message_id is not None:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Modifica",
                    callback_data=f"edit_{message_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Elimina",
                    callback_data=f"delete_{message_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Lista",
                    callback_data="list_messages"
                ),
                InlineKeyboardButton(
                    text="🏠 Menu",
                    callback_data="main_menu"
                )
            ]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Torna alla Lista",
                    callback_data="list_messages"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Menu Principale",
                    callback_data="main_menu"
                )
            ]
        ])
    return keyboard

def confirmation_keyboard(msg_id: int) -> InlineKeyboardMarkup:
    """Tastiera per la conferma dell'eliminazione di un messaggio."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Conferma Eliminazione",
                callback_data=f"confirm_delete_{msg_id}"
            ),
            InlineKeyboardButton(
                text="❌ Annulla",
                callback_data="cancel_delete"
            )
        ]
    ])
    return keyboard