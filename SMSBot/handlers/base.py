from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config.config import config
from keyboards.base import get_main_keyboard
from utils.states import BotStates

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != config.admin_id:
        await message.reply("Mi dispiace, non sei autorizzato ad usare questo bot.")
        return
        
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Invia Messaggio")],
            [KeyboardButton(text="⏰ Messaggi Programmati")],
            [KeyboardButton(text="ℹ️ Info")]
        ],
        resize_keyboard=True
    )
    
    await message.reply(
        "👋 Benvenuto nel bot di gestione messaggi!\n"
        "Usa i pulsanti sottostanti per inviare o programmare messaggi.",
        reply_markup=keyboard
    )

@router.message(Command("cancel"))
@router.message(F.text == '❌ Annulla')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != config.admin_id:
        return
        
    await state.clear()
    await message.reply(
        "❌ Operazione annullata.\n"
        "Cosa vuoi fare?",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == 'ℹ️ Info')
async def show_info(message: types.Message):
    if message.from_user.id != config.admin_id:
        return
        
    info_text = (
        "ℹ️ Informazioni sui gruppi:\n\n"
        f"📱 {config.gruppo_clienti_name}\n"
        f"ID: {config.gruppo_clienti_id}\n\n"
        f"📱 {config.gruppo_reseller_name}\n"
        f"ID: {config.gruppo_reseller_id}\n"
    )
    await message.reply(info_text, reply_markup=get_main_keyboard())

def register_base_handlers(dp: Router):
    """Registra gli handler di base."""
    dp.include_router(router)