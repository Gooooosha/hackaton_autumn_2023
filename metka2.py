import aiohttp
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types
from geopy.geocoders import Nominatim  # Импорт класса Nominatim из geopy
from config import TOKEN

API_TOKEN = TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Инициализируем объект класса Nominatim для преобразования адреса в координаты
geolocator = Nominatim(user_agent="my_geocoder")

async def on_start(msg: types.Message):
    markup = types.ReplyKeyboardRemove()
    await msg.reply("Привет!\nОтправьте адрес для получения метки на карте.", reply_markup=markup)

@dp.message_handler(commands=['get_location'])
async def get_location(msg: types.Message):
    await msg.reply("Отправьте адрес для получения метки на карте.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def address_to_location(msg: types.Message):
    address = msg.text
    location = geolocator.geocode(address)  # Преобразование адреса в координаты

    if location:
        latitude, longitude = location.latitude, location.longitude
        await bot.send_location(msg.chat.id, latitude, longitude)  # Отправка метки на карте
    else:
        await msg.reply("Адрес не найден. Попробуйте ввести другой адрес.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
