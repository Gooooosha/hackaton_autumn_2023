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
    except sr.UnknownValueError:
        await bot.send_message(message.from_user.id, "Бот не расслышал фразу")
    except sr.RequestError:
        await bot.send_message(message.from_user.id, "Ошибка сервиса")
    
if __name__ == '__main__':
    executor.start_polling(dp)