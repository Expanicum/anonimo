from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Invia un messaggio", callback_data="menu_messages")],
        [InlineKeyboardButton(text="📅 Messaggi Programmati", callback_data="menu_scheduled")]
    ])

def messages_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Invia al Gruppo 1", callback_data="send_group_1")],
        [InlineKeyboardButton(text="📤 Invia al Gruppo 2", callback_data="send_group_2")],
        [InlineKeyboardButton(text="🔙 Menu Principale", callback_data="menu_back")]
    ])

def confirm_send_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Conferma", callback_data="confirm_send"),
            InlineKeyboardButton(text="❌ Annulla", callback_data="cancel_send")
        ]
    ])

def pin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📌 Sì", callback_data="pin_yes"),
            InlineKeyboardButton(text="❌ No", callback_data="pin_no")
        ]
    ])