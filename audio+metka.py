from aiogram import types
from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types
from geopy.geocoders import Nominatim
from config import TOKEN
from aiogram import Bot
from aiogram.types import ContentType, Message
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config import TOKEN
import soundfile as sf
import speech_recognition as sr

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
r = sr.Recognizer()

# Инициализируем объект класса Nominatim для преобразования адреса в координаты
geolocator = Nominatim(user_agent="my_geocoder")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def address_to_location(msg: types.Message):
    address = msg.text
    location = geolocator.geocode(address)  # Преобразование адреса в координаты

    if location:
        latitude, longitude = location.latitude, location.longitude
        await bot.send_location(msg.chat.id, latitude, longitude)  # Отправка метки на карте
    else:
        await msg.reply("Адрес не найден. Попробуйте ввести другой адрес.")

@dp.message_handler(content_types=[ContentType.VOICE])
async def voice_message_handler(message: Message):
    voice = await message.voice.get_file()
    await bot.download_file(file_path=voice.file_path, destination=f"./voices/{voice.file_id}.ogg")
    data, samplerate = sf.read(f"./voices/{voice.file_id}.ogg")
    sf.write(f"./voices/{voice.file_id}.wav", data, samplerate)
    file = sr.AudioFile(f"./voices/{voice.file_id}.wav")
    try:
        with file as source:
            audio = r.record(source)
            result = r.recognize_google(audio,language='ru-RU')
        await bot.send_message(message.from_user.id, result)
        location = geolocator.geocode(result)  # Преобразование адреса в координаты
        if location:
            latitude, longitude = location.latitude, location.longitude
            await bot.send_location(message.chat.id, latitude, longitude)  # Отправка метки на карте
        else:
            await message.reply("Адрес не найден. Попробуйте ввести другой адрес.")
    except sr.UnknownValueError:
        await bot.send_message(message.from_user.id, "Бот не расслышал фразу")
    except sr.RequestError:
        await bot.send_message(message.from_user.id, "Ошибка сервиса")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)