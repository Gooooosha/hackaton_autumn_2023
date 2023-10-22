from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup

class States(StatesGroup):
    START = State()
    NAME = State()
    AGE = State()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())