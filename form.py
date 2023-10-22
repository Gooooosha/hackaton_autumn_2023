from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
class States(StatesGroup):
    START = State()  # начальное состояние
    NAME = State()   # состояние, где запрашивается имя пользователя
    AGE = State()    # состояние, где запрашивается возраст пользователя

 
# инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(state=States.START, commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет! Как тебя зовут?")
    await States.NAME.set()
 
@dp.message_handler(state=States.NAME)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply(f"Привет, {message.text}! Сколько тебе лет?")
    await States.AGE.set()
 
@dp.message_handler(state=States.AGE)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    user_data = await state.get_data()
    await message.reply(f"Тебе {user_data['age']} лет, {user_data['name']}!")
    await state.finish()

if __name__ == "__main__":
    dp.register_message_handler(process_start_command, commands=['start'], state="*") 
    executor.start_polling(dp)