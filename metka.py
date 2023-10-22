import aiohttp
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types
from config import TOKEN
API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def on_start(msg: types.Message):
    markup = types.ReplyKeyboardRemove()
    await msg.reply("Привет!\nОтправьте метку (координаты) для получения адреса.", reply_markup=markup)

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def get_address(msg: types.Message):
    location = msg.location
    latitude = location.latitude
    longitude = location.longitude

    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}') as resp:
            data = await resp.json()
            display_name = data.get('display_name', 'Адрес не найден')

            await msg.reply(f"Координаты: {latitude}, {longitude}\nАдрес: {display_name}", parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)