from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_message = State()
    waiting_for_schedule = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_recurrence = State()
    waiting_for_days = State()
    waiting_for_pin = State()
    waiting_for_message_id = State()