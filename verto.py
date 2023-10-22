import telebot
import sqlite3
from telebot import types
import re

# Подключение бота
bot = telebot.TeleBot("5541236789:AAEyepDiUO5RQBzKdMpEN1uElkCkVGfs_MU")

# Подключение к БД
conn = sqlite3.connect("db/database.db", check_same_thread=False)
cursor = conn.cursor()

# Команда start
@bot.message_handler(commands=["start"])
def start(m):
    if m.chat.type == "private":

        # Если start передается с параметрами:
        if len(m.text.split()) == 2:
            cursor.execute("SELECT * FROM deals where id_deals = ?", (m.text.split()[1], ))
            record = cursor.fetchone()
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Принять", callback_data = "y" + str(m.text.split()[1]) + " " + str(m.from_user.id)))
            keyboard.add(types.InlineKeyboardButton(text="Отклонить", callback_data = "n"+ str(m.text.split()[1]) + " " + str(m.from_user.id)))
            if m.from_user.last_name == None:
                bot.send_message(record[1], "Исполнитель " + m.from_user.first_name + " готов выполнить ваше [задание](" + "https://t.me/vertoggf/" + str(record[6]) + ")" + "!", parse_mode = "Markdown", reply_markup = keyboard)
            else:
                bot.send_message(record[1], "Исполнитель " + m.from_user.first_name + " " + str(m.from_user.last_name) + " готов выполнить ваше [задание](" + "https://t.me/vertoggf/" + str(record[6]) + ")" + "!", parse_mode = "Markdown", reply_markup=keyboard)
            bot.send_message(m.chat.id, "Запрос отправлен!")

        # Добавляем кнопку
        else:
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1=types.KeyboardButton("Новый пост")
            markup.add(item1)
            bot.send_message(m.chat.id, "Привет😎",  reply_markup=markup)

# Команда menu
@bot.message_handler(commands=["menu"])
def menu(m):

    if m.chat.type == "private":
        bot.send_message(m.chat.id, "С помощью этого бота, вы можете размещать и выполнять задания на канале [Главный](https://t.me/vertoggf)\n\nПеречень доступных команд:\n\n*Новый пост* - опубликовать пост на канале", parse_mode = "Markdown")
    elif cursor.execute('SELECT * FROM deals WHERE id_chat = ?', (m.chat.id, )).fetchone() is not None:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Указать цену 💰", callback_data = "cost"))
        keyboard.add(types.InlineKeyboardButton(text="Отменить сделку ❌", callback_data = "cancel"))
        keyboard.add(types.InlineKeyboardButton(text="Позвать админа ⚠️", callback_data = "admin"))
        bot.send_message(m.chat.id, "Выберите кнопку меню", reply_markup = keyboard)
# Ответы на кнопки
@bot.callback_query_handler(func = lambda call:True)
def callback(call):
    if call.message:
        if call.data[0] == "y":
            y = call.data.replace("y","").split()[0]
            yz = call.data.replace("y","").split()[1]
            cursor.execute("SELECT * FROM deals where id_deals = ?", (y, ))
            record = cursor.fetchone()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text = "Перейти в чат", url = "https://t.me/+rrIYQE8DB700YjBi"))
            bot.send_message(yz, "Ваш запрос на [пост](" + "https://t.me/vertoggf/" + str(record[6]) + ")" + " принят🙂", parse_mode = "Markdown", reply_markup = keyboard)
            bot.send_message(record[1], "Вы успешно приняли запрос на [пост](" + "https://t.me/vertoggf/" + str(record[6]) + ")", parse_mode = "Markdown", reply_markup = keyboard)
            cursor.execute("Update deals set id_chat = ? where id_deals = ?",(-784162684, y))
            cursor.execute("Update deals set id_executor = ? where id_deals = ?",(yz, y))
            conn.commit()
        elif call.data[0] == "n":
            n = call.data.replace("n","").split()[0]
            nz = call.data.replace("n","").split()[1]
            cursor.execute("SELECT * FROM deals where id_deals = ?", (n, ))
            record = cursor.fetchone()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(nz, "Ваш запрос отклонен😔")
        elif call.data == "cost":
            cursor.execute("SELECT * FROM deals where id_chat = ?", (call.message.chat.id, ))
            record = cursor.fetchone()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.register_next_step_handler(bot.send_message(call.message.chat.id, "Текущая стоимость сделки: " + str(record[5]) + "\n\nЧтоб указать цену сделки, оба участика должны отправить обговоренную сумму за задание.\n\nКомиисия сервиса:\nОт 20 руб. до 50 руб. - 5 руб.\nОт 51 руб. до 200 руб. - 10 руб.\nОт 201 руб. и выше - 5%\n\nМинимальная цена сделки: 20 руб.\n\n*Цена должна быть указана только числом."), cost_save)

# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.chat.type == "private":

        # Если юзер прислал Новый пост, начинается создание поста в диалоговом режиме
        if message.text == "Новый пост" :

            # Режим диалога
            title_request = bot.send_message(message.chat.id, "Отправьте название предмета или задания")
            bot.register_next_step_handler(title_request, title_save)

            # Одобрение поста по отправленному +
        elif message.text[0] == '+' and message.from_user.id == 640659782:
            id_accept = message.text.replace("+","")
            cursor.execute("SELECT * FROM deals where id_deals = ?", (id_accept, ))
            record = cursor.fetchone()
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text = "Взять", url = "https://t.me/vertovivo_bot?start=" + str(id_accept)))
            new_post = bot.send_message(-1001667640177, "🔵 Активно\n\n" + "*" + str(record[3]) + "*" + "\n\n" + str(record[4]) + "\n\nЦена: " + str(record[5]) + "р", reply_markup = keyboard, parse_mode = "Markdown")
            bot.send_message(record[1], "Ваш [пост](" + "https://t.me/vertoggf/" + str(new_post.message_id) + ")" + " опубликован👍", parse_mode = "Markdown")
            cursor.execute("Update deals set id_deals_in_group = ? where id_deals = ?",(new_post.message_id, id_accept))
            conn.commit()

            # Отклонение поста по отправленному -
        elif message.text[0] == '-' and message.from_user.id == 640659782:
            id_accept = message.text.replace("-","")
            cursor.execute("SELECT * FROM deals where id_deals = ?", (id_accept, ))
            record = cursor.fetchone()
            bot.send_message(record[1], "Ваш пост отклонен...")
# Функция проверки на содержание цифр
def contains_digits(d):
    _digits = re.compile('\d')
    return bool(_digits.search(d))

# Функция для отправки id сделки админу на одобрение
def deal_approval(id_deal_, title_, description_, cost_):
    bot.send_message(640659782, "🔵 Активно #<code>" + str(id_deal_) + "</code>\n\n" + "<b>" + str(title_) + "</b>" + "\n\n" + str(description_) + "\n\nЦена: " + str(cost_) + "р", parse_mode= "HTML")

# Функция запроса названия сделки
def title_save(message):
    global title
    title = message.text
    description_request = bot.send_message(message.chat.id, "Максимально детально опишите задание")
    bot.register_next_step_handler(description_request, description_save)

# Функция запроса описания сделки
def description_save(message):
    global description
    description = message.text
    price_request = bot.send_message(message.chat.id, "Отправьте цену за задание")
    bot.register_next_step_handler(price_request, price_save)

# Функция запроса стоимости сделки
def price_save(message):
    conn.create_function("approval", 4, deal_approval)
    price = int(message.text)
    bot.send_message(message.chat.id, "Пост готов! Идёт проверка...")
    bot.send_message(message.chat.id, "🔵 Активно\n\n" + "*" + title + "*" + "\n\n" + description + "\n\nЦена: " + str(price) + "р", parse_mode = "Markdown")
    cursor.execute("INSERT INTO deals (id_customer, title, description, cost, price) VALUES (?, ?, ?, ?, ?)", (message.from_user.id, title, description, price, price))
    conn.commit()

# Функция запроса стоимости сделки от двух участников
def cost_save(message):
    if message.text == "/menu@vertovivo_bot" or message.text == "/menu":
        menu(message)
    elif contains_digits(message.text) and not message.text.isdigit():
        bot.send_message(message.chat.id, "Стоимость должна быть указана только целым числом!\nПопробуйте ещё раз...")
        bot.register_next_step_handler(message, cost_save)
    elif not message.text.isdigit():
        bot.register_next_step_handler(message, cost_save)
    elif int(message.text) < 20:
        bot.send_message(message.chat.id, "Минимальная стоимость сделки 20 рублей!\nПопробуйте ещё раз...")
        bot.register_next_step_handler(message, cost_save)
    else:
        cursor.execute("SELECT * FROM deals where id_chat = ?", (message.chat.id, ))
        record = cursor.fetchone()
        if record[1] == message.from_user.id:
            cursor.execute("Update deals set cost_upd2 = ? where id_chat = ?",(message.text, message.chat.id))
            conn.commit()
        elif record[2] == message.from_user.id:
            cursor.execute("Update deals set cost_upd = ? where id_chat = ?",(message.text, message.chat.id))
            conn.commit()
        cursor.execute("SELECT * FROM deals where id_chat = ?", (message.chat.id, ))
        record = cursor.fetchone()
        if record[8] == 0 or record[9] == 0:
            bot.register_next_step_handler(message, cost_save)
        else:
            if record[8] == record[9]:
                bot.send_message(message.chat.id, "Стоимость принята!")
                cursor.execute("Update deals set cost_upd = ? where id_chat = ?",(0, message.chat.id))
                cursor.execute("Update deals set cost_upd2 = ? where id_chat = ?",(0, message.chat.id))
                cursor.execute("Update deals set price = ? where id_chat = ?",(record[8], message.chat.id))
                conn.commit()
                
            else:
                bot.send_message(message.chat.id, "Указана разная стоимость!\nПопробуйте ещё раз...")
                bot.register_next_step_handler(message, cost_save)

# Запускаем бота
bot.polling(none_stop=True, interval=0)