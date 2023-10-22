from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import executor
import psycopg2
import aiohttp
import easyocr
from aiogram.types import ParseMode
import speech_recognition as sr
import soundfile as sf
from geopy.geocoders import Nominatim
from datetime import datetime
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))

class States(StatesGroup):
    CONTRACT_NUMBER = State()
    PASSWORD = State()
    PASSPORT = State()

class States_Manager(StatesGroup):
    LOGIN = State()
    PASSWORD_MANAGER = State()

class States_waybill(StatesGroup):
    SENDING_MODE = State()
    NUMBER_OF_PLACES = State()
    DESCRIPTION_OF_ATTACHMENTS = State()
    WEIGHT_OF_EACH_SEAT = State()
    COST_OF_INVESTMENT = State()
    DELIVERY_ADDRESS = State()
    STORE_ADDRESS = State()
    ADDRESS = State()
    METHOD_OF_PAYMENT = State()

# инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
geolocator = Nominatim(user_agent="my_geocoder")
r = sr.Recognizer()

# Создаем кнопку "Авторизация"
authorization_button = types.KeyboardButton("Авторизация в статусе клиента 👫")
authorization_button_manager = types.KeyboardButton("Авторизация в статусе менеджера 👩🏻‍💻")
authorization_markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(authorization_button).add(authorization_button_manager)

# Создаем кнопку "Отмена"
cancel_button = types.KeyboardButton("Отмена ❌")
cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_button)

# Создаем кнопку "Отмена"
cancel_button = types.KeyboardButton("Отмена создания накладной ❌")
cancel_markup_waybill = types.ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_button)

buttons = [
    #types.KeyboardButton("1"),
    #types.KeyboardButton("2"),
    types.KeyboardButton("Выйти 🚪"),
]
custom_manager = types.ReplyKeyboardMarkup(resize_keyboard=True)
custom_manager.add(*buttons)

buttons = [
    types.KeyboardButton("Создать накладную 📃"),
    types.KeyboardButton("Позвать менеджера 📲"),
    types.KeyboardButton("Регистрация претензии 😑"),
    types.KeyboardButton("Выйти 🚪"),
]
custom_client = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
custom_client.add(*buttons)

@dp.message_handler(Command("start"), state="*")
async def process_start_command(message: types.Message):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM manager WHERE tg_id = %s", (str(message.from_user.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        await message.reply("Приветствуем менеджера ✅", reply_markup=custom_manager)
        return
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM client WHERE tg_id = %s", (str(message.from_user.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        await message.reply("Приветствуем клиента ✅", reply_markup=custom_client)
        return
    await message.reply("Привет! Авторизируйся! 🔆", reply_markup=authorization_markup)

@dp.message_handler(Text(equals="Отмена ❌"), state="*")
async def process_cancel(message: types.Message, state: FSMContext):
    await message.reply("Авторизация отменена.", reply_markup=authorization_markup)
    await state.finish()

@dp.message_handler(Text(equals="Отмена создания накладной ❌"), state="*")
async def process_cancel(message: types.Message, state: FSMContext):
    await message.reply("Создание накладной отменено", reply_markup=custom_client)
    await state.finish()

@dp.message_handler(Text(equals="Авторизация в статусе клиента 👫"), state="*")
async def process_authorization(message: types.Message):
    await message.reply("Для авторизации, введите номер договора:", reply_markup=cancel_markup)
    await States.CONTRACT_NUMBER.set()

@dp.message_handler(state=States.CONTRACT_NUMBER)
async def process_contract_number(message: types.Message, state: FSMContext):
    await state.update_data(contract_number=message.text)
    await message.reply("Теперь введите пароль:", reply_markup=cancel_markup)
    await States.PASSWORD.set()

@dp.message_handler(state=States.PASSWORD)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.reply("Теперь введите паспорт:", reply_markup=cancel_markup)
    await States.PASSPORT.set()

@dp.message_handler(state=States.PASSPORT, content_types=[types.ContentType.PHOTO])
async def process_passport_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    photo_file_id = photo.file_id
    file = await bot.get_file(photo_file_id)
    await file.download('./pasp/photo.jpg')
    result = []
    reader = easyocr.Reader(['ru'])  
    image = './pasp/photo.jpg'
    texts = reader.readtext(image)
    for (bbox, text, prob) in texts:
        result.append(text)
    result = ''.join(result[:3])
    await state.update_data(passport=result)
    user_data = await state.get_data()
    is_authenticated = check_authentication_client(user_data['contract_number'], user_data['password'], user_data['passport'])
    if is_authenticated:
        await message.reply(f"Авторизация успешна, добро пожаловать, {user_data['contract_number']}!", reply_markup=types.ReplyKeyboardRemove())
        
        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cur = conn.cursor()
        cur.execute("SELECT tg_id FROM manager WHERE tg_id <> '0' ORDER BY clients ASC LIMIT 1")
        manager_tg_id = cur.fetchone()
        cur.close()
        conn.close()

        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        update_query = "UPDATE client SET tg_id = %s, password = %s, manager = %s WHERE number = %s"
        cursor.execute(update_query, (message.from_user.id, user_data['password'], manager_tg_id[0], user_data['contract_number']))
        conn.commit()
        conn.close()

        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        cursor.execute('SELECT clients FROM manager WHERE tg_id = %s', (manager_tg_id[0],))
        clients_manager = cursor.fetchone()
        update_query = "UPDATE manager SET clients = %s WHERE tg_id = %s"
        cursor.execute(update_query, (str(int(clients_manager[0]) + 1), manager_tg_id[0]))
        conn.commit()
        conn.close()
        
        await message.reply("Выберите действие:", reply_markup=custom_client)
    else:
        await message.reply("Неверные данные для входа", reply_markup=authorization_markup)
    await state.finish()

# Функция для проверки авторизации клиента (замените на вашу логику)
def check_authentication_client(contract_number, password, passport):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                            password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM Client WHERE number = %s AND passport = %s', (contract_number,passport))
    client_password = cursor.fetchone()
    conn.close()
    try:
        return password == client_password[0]
    except:
        return False

@dp.message_handler(Text(equals="Авторизация в статусе менеджера 👩🏻‍💻"), state="*")
async def process_authorization(message: types.Message):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM manager WHERE tg_id = %s", (str(message.from_user.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        await message.reply("Вы уже авторизованы, как менеджер")
        return
    await message.reply("Для авторизации, введите логин:", reply_markup=cancel_markup)
    await States_Manager.LOGIN.set()

@dp.message_handler(state=States_Manager.LOGIN)
async def process_contract_number(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.reply("Теперь введите пароль:", reply_markup=cancel_markup)
    await States_Manager.PASSWORD_MANAGER.set()

@dp.message_handler(state=States_Manager.PASSWORD_MANAGER)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    user_data = await state.get_data()
    # Проверка номера договора и пароля здесь (ваша логика проверки)
    is_authenticated = check_authentication_manager(user_data['login'], user_data['password'])
    if is_authenticated:
        await message.reply(f"Авторизация успешна, добро пожаловать, {user_data['login']}!", reply_markup=types.ReplyKeyboardRemove())
        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        update_query = "UPDATE manager SET password = %s, tg_id = %s WHERE login = %s"

        cursor.execute(update_query, (user_data['password'], message.from_user.id, user_data['login']))
        conn.commit()
        conn.close()
        
        await message.reply("Выберите действие:", reply_markup=custom_manager)
    else:
        await message.reply("Неверный номер договора или пароль. Попробуйте снова.", reply_markup=authorization_markup)
    await state.finish()

#Функция для проверки авторизации менеджера (замените на вашу логику)
def check_authentication_manager(login, password):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM Manager WHERE login = %s', (login,))
    client_password = cursor.fetchone()
    conn.close()
    try:
        return password == client_password[0]
    except:
        return False

# Создайте клавиатуру с двумя инлайн кнопками
keyboard = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("дверь-дверь", callback_data="дверь-дверь")
button2 = types.InlineKeyboardButton("склад-склад", callback_data="склад-склад")
button3 = types.InlineKeyboardButton("склад-дверь", callback_data="склад-дверь")
button4 = types.InlineKeyboardButton("дверь-склад", callback_data="дверь-склад")
keyboard.row(button1)
keyboard.row(button2)
keyboard.row(button3)
keyboard.row(button4)

@dp.message_handler(lambda message: message.text == "Создать накладную 📃")
async def create_invoice(message: types.Message):
    await message.reply("🔸Чтобы отменить, нажмите 'Отмена создания накладной'", reply_markup=cancel_markup_waybill)
    await message.reply("🔹Выберите режим отправки", reply_markup=keyboard)
    await States_waybill.SENDING_MODE.set()

@dp.callback_query_handler(lambda query: query.data in ['дверь-дверь', 'склад-склад', 'склад-дверь', 'дверь-склад'], state=States_waybill.SENDING_MODE)
async def process_sending_mode(query: types.CallbackQuery, state: FSMContext):
    sending_mode = query.data
    await state.update_data(sending_mode=sending_mode)
    await bot.edit_message_text(chat_id=query.message.chat.id, text=f"🔹Выберите режим отправки: {sending_mode}", message_id=query.message.message_id)
    await query.message.answer("🔹Выберите количество мест")
    await States_waybill.NUMBER_OF_PLACES.set()

@dp.message_handler(state=States_waybill.NUMBER_OF_PLACES)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(number_of_places=message.text)
    await message.reply("🔹Опишите вложения через ;", reply_markup=cancel_markup_waybill)
    await States_waybill.DESCRIPTION_OF_ATTACHMENTS.set()

@dp.message_handler(state=States_waybill.DESCRIPTION_OF_ATTACHMENTS)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(description_of_attachments=message.text)
    await message.reply("🔹Опишите вес каждого места через ;", reply_markup=cancel_markup_waybill)
    await States_waybill.WEIGHT_OF_EACH_SEAT.set()

keyboard2 = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("общая", callback_data="общая")
button2 = types.InlineKeyboardButton("по местам", callback_data="по местам")
keyboard2.row(button1)
keyboard2.row(button2)

@dp.message_handler(state=States_waybill.WEIGHT_OF_EACH_SEAT)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(weight_of_each_seat=message.text)
    await message.reply("🔸Чтобы отменить, нажмите 'Отмена создания накладной'", reply_markup=cancel_markup_waybill)
    await message.reply("🔹Выберите стоимость вложения", reply_markup=keyboard2)
    await States_waybill.COST_OF_INVESTMENT.set()

keyboard3 = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("ПВЗ", callback_data="ПВЗ")
button2 = types.InlineKeyboardButton("К двери", callback_data="К двери")
keyboard3.row(button1)
keyboard3.row(button2)

@dp.callback_query_handler(lambda query: query.data in ['общая', 'по местам'], state=States_waybill.COST_OF_INVESTMENT)
async def process_sending_mode(query: types.CallbackQuery, state: FSMContext):
    sending_mode = query.data
    await state.update_data(cost_of_investment=sending_mode)
    await bot.edit_message_text(chat_id=query.message.chat.id, text=f"🔹Выберите стоимость вложения: {sending_mode}", message_id=query.message.message_id)
    await query.message.answer("🔹Выберите тип доставки", reply_markup=keyboard3)
    await States_waybill.DELIVERY_ADDRESS.set()

keyboard4 = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("ПВЗ(1)", callback_data="ПВЗ(1)")
button2 = types.InlineKeyboardButton("ПВЗ(2)", callback_data="ПВЗ(2)")
button3 = types.InlineKeyboardButton("ПВЗ(3)", callback_data="ПВЗ(3)")
button4 = types.InlineKeyboardButton("ПВЗ(4)", callback_data="ПВЗ(4)")
button5 = types.InlineKeyboardButton("ПВЗ(5)", callback_data="ПВЗ(5)")
keyboard4.row(button1)
keyboard4.row(button2)
keyboard4.row(button3)
keyboard4.row(button4)
keyboard4.row(button5)

@dp.callback_query_handler(lambda query: query.data in ['ПВЗ', 'К двери'], state=States_waybill.DELIVERY_ADDRESS)
async def process_sending_mode(query: types.CallbackQuery, state: FSMContext):
    sending_mode = query.data
    await state.update_data(delivery_address=sending_mode)
    await bot.edit_message_text(chat_id=query.message.chat.id, text=f"🔹Выберите тип доставки: {sending_mode}", message_id=query.message.message_id)
    if sending_mode == 'ПВЗ':
        await query.message.answer("🔹Выберите ПВЗ", reply_markup=keyboard4)
        await States_waybill.STORE_ADDRESS.set()
    else:
        await query.message.answer("🔹Выберите адрес")
        await States_waybill.ADDRESS.set()


keyboard5 = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("Оплата получателем", callback_data="Оплата получателем")
button2 = types.InlineKeyboardButton("Отправителем по договору", callback_data="Отправителем по договору")
keyboard5.row(button1)
keyboard5.row(button2)

@dp.message_handler(state=States_waybill.ADDRESS, content_types=[types.ContentType.TEXT])
async def process_text_address(message: types.Message, state: FSMContext):
    address = message.text
    location = geolocator.geocode(address)  # Преобразование адреса в координаты

    if location:
        latitude, longitude = location.latitude, location.longitude
        await bot.send_location(message.chat.id, latitude, longitude)  # Отправка метки на карте
        async with aiohttp.ClientSession() as session:
                async with session.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}') as resp:
                    data = await resp.json()
                    address = ""

                    if 'address' in data:
                        if 'city' in data['address']:
                            address += f"Город: {data['address']['city']}\n"
                        if 'road' in data['address']:
                            address += f"Улица: {data['address']['road']}\n"
                        if 'house_number' in data['address']:
                            address += f"Дом: {data['address']['house_number']}\n"
                    else:
                        address += 'Адрес не найден'

                    await message.reply(address, parse_mode=ParseMode.HTML)
    else:
        await message.reply("Адрес не найден. Попробуйте ввести другой адрес.")
    await state.update_data(address=address)
    await message.reply("🔹Выберите способ оплаты", reply_markup=keyboard5)
    await States_waybill.METHOD_OF_PAYMENT.set()

@dp.message_handler(state=States_waybill.ADDRESS, content_types=[types.ContentType.VOICE])
async def process_voice_address(message: types.Message, state: FSMContext):
    voice = await message.voice.get_file()
    await bot.download_file(file_path=voice.file_path, destination=f"./voices/{voice.file_id}.ogg")
    data, samplerate = sf.read(f"./voices/{voice.file_id}.ogg")
    sf.write(f"./voices/{voice.file_id}.wav", data, samplerate)
    file = sr.AudioFile(f"./voices/{voice.file_id}.wav")
    try:
        with file as source:
            audio = r.record(source)
            result = r.recognize_google(audio,language='ru-RU')
        location = geolocator.geocode(result)  # Преобразование адреса в координаты
        if location:
            latitude, longitude = location.latitude, location.longitude
            await bot.send_location(message.chat.id, latitude, longitude)  # Отправка метки на карте
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}') as resp:
                    data = await resp.json()
                    address = ""

                    if 'address' in data:
                        if 'city' in data['address']:
                            address += f"Город: {data['address']['city']}\n"
                        if 'road' in data['address']:
                            address += f"Улица: {data['address']['road']}\n"
                        if 'house_number' in data['address']:
                            address += f"Дом: {data['address']['house_number']}\n"
                    else:
                        address += 'Адрес не найден'

                    await message.reply(address, parse_mode=ParseMode.HTML)
        else:
            await message.reply("Адрес не найден. Попробуйте ввести другой адрес.")
    except sr.UnknownValueError:
        await bot.send_message(message.from_user.id, "Бот не расслышал фразу")
    except sr.RequestError:
        await bot.send_message(message.from_user.id, "Ошибка сервиса")

    await state.update_data(address=address)
    await message.reply("🔹Выберите способ оплаты", reply_markup=keyboard5)
    await States_waybill.METHOD_OF_PAYMENT.set()

@dp.message_handler(state=States_waybill.ADDRESS, content_types=[types.ContentType.LOCATION])
async def process_location_address(message: types.Message, state: FSMContext):
    # Обработка геолокации
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}') as resp:
            data = await resp.json()
            address = ""

            if 'address' in data:
                if 'city' in data['address']:
                    address += f"Город: {data['address']['city']}\n"
                if 'road' in data['address']:
                    address += f"Улица: {data['address']['road']}\n"
                if 'house_number' in data['address']:
                    address += f"Дом: {data['address']['house_number']}\n"
            else:
                address += 'Адрес не найден'

            await message.reply(address, parse_mode=ParseMode.HTML)
    await state.update_data(address=address)
    await message.reply("🔹Выберите способ оплаты", reply_markup=keyboard5)
    await States_waybill.METHOD_OF_PAYMENT.set()

@dp.callback_query_handler(lambda query: query.data in ['ПВЗ(1)', 'ПВЗ(2)', 'ПВЗ(3)', 'ПВЗ(4)', 'ПВЗ(5)'], state=States_waybill.STORE_ADDRESS)
async def process_sending_mode(query: types.CallbackQuery, state: FSMContext):
    sending_mode = query.data
    await state.update_data(address=sending_mode)
    await bot.edit_message_text(chat_id=query.message.chat.id, text=f"🔹Выберите ПВЗ: {sending_mode}", message_id=query.message.message_id)
    await query.message.answer("🔹Выберите способ оплаты", reply_markup=keyboard5)
    await States_waybill.METHOD_OF_PAYMENT.set()

@dp.callback_query_handler(lambda query: query.data in ['Оплата получателем', 'Отправителем по договору'], state=States_waybill.METHOD_OF_PAYMENT)
async def process_sending_mode(query: types.CallbackQuery, state: FSMContext):
    sending_mode = query.data
    await state.update_data(method_of_payment=sending_mode)
    await bot.edit_message_text(chat_id=query.message.chat.id, text=f"🔹Выберите способ оплаты: {sending_mode}", message_id=query.message.message_id)
    
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    insert_query = "INSERT INTO waybill (tg_id, date) VALUES (%s, %s) RETURNING number"
    cursor.execute(insert_query, (query.from_user.id, f"{datetime.now().day}.{datetime.now().month}.{datetime.now().year}"))
    number = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    await query.message.answer(f"🎉 Накладная #{number} успешно создана 🎉", reply_markup=custom_client)
    waybill_data = await state.get_data()
    print(waybill_data)

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Arial', 9)

    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute('SELECT fio, number FROM client WHERE tg_id = %s', (str(query.from_user.id),))
    client_fio = cursor.fetchone()
    conn.close()

    can.drawString(255, 777, str(number))
    can.drawString(300, 777, str(datetime.now().day))
    can.drawString(325, 777, str(datetime.now().month))
    can.drawString(345, 777, str(datetime.now().year))
    can.drawString(110, 655, client_fio[0])
    can.drawString(400, 655, client_fio[1])
    can.drawString(140, 618, waybill_data['sending_mode'])
    description_of_attachments = waybill_data['description_of_attachments'].split(';')
    weight_of_each_seat = waybill_data['weight_of_each_seat'].split(';')
    left = 80
    bottom = 550
    for i in range(len(description_of_attachments)):
        can.drawString(left, bottom, description_of_attachments[i])
        can.drawString(left + 130, bottom, weight_of_each_seat[i])
        can.drawString(left + 215, bottom, waybill_data['cost_of_investment'])
        bottom -= 28
    can.drawString(140, 350, waybill_data['address'])
    can.drawString(140, 310, waybill_data['method_of_payment'])

    can.showPage()
    can.save()
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    existing_pdf = PdfFileReader(open("pattern.pdf", "rb"))
    output = PdfFileWriter()
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    pdf_filename = f"./waybill/{number}.pdf"
    outputStream = open(pdf_filename, "wb")
    output.write(outputStream)
    outputStream.close()
    with open(pdf_filename, "rb") as pdf_file:
        await bot.send_document(chat_id=query.message.chat.id, document=types.InputFile(pdf_file))

    await state.finish()

@dp.message_handler(lambda message: message.text == "Позвать менеджера 📲")
async def call_manager(message: types.Message):
    
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, url FROM chat WHERE status = '0' LIMIT 1")
    record = cursor.fetchone()
    if record == None:
        await message.reply("Все чаты заняты!", reply_markup=custom_client)
        return
    conn.close()
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute("SELECT manager FROM client WHERE tg_id = %s", (str(message.from_user.id),))
    manager = cursor.fetchone()
    conn.close()
    
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    update_query = "UPDATE chat SET client = %s, manager = %s, status = 1 WHERE chat_id = %s"
    cursor.execute(update_query, (str(message.from_user.id), manager[0], record[0]))
    conn.commit()
    conn.close()

    link_button = types.InlineKeyboardButton(text="Перейти", url=record[1])
    keyboard = types.InlineKeyboardMarkup().add(link_button)
    await bot.send_message(manager[0], "Клиент вызывает вас в чат...", reply_markup=keyboard)
    await bot.send_message(message.from_user.id, "Менеджер скоро будет...", reply_markup=keyboard)


@dp.message_handler(commands=['help'])
async def finish_command(message: types.Message):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT * FROM chat WHERE chat_id = %s", (str(message.chat.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        keyboard = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="Подтвердить", callback_data="continue_help")
        keyboard.add(button)
        await bot.send_message(message.chat.id, "Вопрос решен?", reply_markup=keyboard)
    else:
        await bot.send_message(message.from_user.id, "Комания ИКТИН - это топ!", reply_markup=keyboard)

@dp.callback_query_handler(lambda query: query.data == "continue_help")
async def continue_help(query: types.CallbackQuery):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT * FROM chat WHERE chat_id = %s", (str(query.message.chat.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    user1 = result[2]
    user2 = result[3]
    await bot.kick_chat_member(chat_id=query.message.chat.id, user_id=user1)
    await bot.kick_chat_member(chat_id=query.message.chat.id, user_id=user2)
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cursor = conn.cursor()
    update_query = "UPDATE chat SET client = 0, manager = 0, status = 0 WHERE chat_id = %s"
    cursor.execute(update_query, (str(query.message.chat.id), ))
    conn.commit()
    conn.close()
    await bot.delete_message(query.message.chat.id, query.message.message_id)
        

@dp.message_handler(lambda message: message.text == "Регистрация претензии 😑")
async def register_complaint(message: types.Message):
    await message.reply("Вы нажали 'Регистрация претензии'.")

# Обработчики нажатий на кнопки
@dp.message_handler(lambda message: message.text == "1")
async def create_invoice(message: types.Message):
    await message.reply("Вы нажали 1")

@dp.message_handler(lambda message: message.text == "2")
async def call_manager(message: types.Message):
    await message.reply("Вы нажали 2")

@dp.message_handler(lambda message: message.text == "Выйти 🚪")
async def register_complaint(message: types.Message):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM manager WHERE tg_id = %s", (str(message.from_user.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        update_query = "UPDATE manager SET tg_id = 0 WHERE tg_id = %s"
        cursor.execute(update_query, (str(message.from_user.id),))
        conn.commit()
        conn.close()
        await message.reply("Вы вышли из аккаунта менеджера", reply_markup=authorization_markup)
        return
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM client WHERE tg_id = %s", (str(message.from_user.id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is not None:
        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        cursor.execute('SELECT manager FROM client WHERE tg_id = %s', (str(message.from_user.id),))
        manager = cursor.fetchone()
        cursor.execute('SELECT clients FROM manager WHERE tg_id = %s', (manager[0],))
        clients = cursor.fetchone()
        update_query = "UPDATE manager SET clients = %s WHERE tg_id = %s"
        cursor.execute(update_query, (str(int(clients[0]) - 1), manager[0]))
        conn.commit()
        conn.close()
        conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                        password='egor123', host='localhost')
        cursor = conn.cursor()
        update_query = "UPDATE client SET tg_id = 0, manager = 0 WHERE tg_id = %s"
        cursor.execute(update_query, (str(message.from_user.id),))
        conn.commit()
        conn.close()
        await message.reply("Вы вышли из аккаунта клиента", reply_markup=authorization_markup)
        return

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)