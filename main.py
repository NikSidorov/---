import requests
import json
from telebot import types
import sqlite3
from config import bot, API_openweathermap


@bot.message_handler(commands=['start'], content_types=['text'])
def welcome(message):
    """
    Функция отправляет пользователю тематическое изображение, приветствие,
    добавляет в базу данных users.bd его уникальный id и имя,
    после чего запрашивает интересующий его город.
    """

    markup = types.ReplyKeyboardMarkup()
    moscow = types.KeyboardButton('Москва')
    spb = types.KeyboardButton('Санкт-Петербург')
    markup.row(moscow, spb)
    sochi = types.KeyboardButton('Сочи')
    russa = types.KeyboardButton('Старая Русса')
    kotlas = types.KeyboardButton('Котлас')
    markup.row(sochi, kotlas, russa)

    image = 'weather_icons.jpg'
    image_file = open('Img/' + image, 'rb')
    bot.send_photo(message.chat.id, image_file)
    image_file.close()

    conn = sqlite3.connect('./users.db', check_same_thread=False)
    cursor = conn.cursor()

    us_id = message.from_user.id

    us_name = message.from_user.first_name
    cursor.execute('INSERT OR REPLACE INTO users (user_id, user_name) '
                   'VALUES (?, ?)',
                   (us_id, us_name))
    conn.commit()
    cursor.close()
    mem = message.from_user.username

    bot.send_message(message.chat.id, f"Привет, {us_name}! \n"
                                      "Запомни, а то забудешь: я - бот, предоставляющий прогноз погоды.\n"
                                      "Какой город тебя интересует? Можешь ввести или выбрать из предложенных городов:",
                     reply_markup=markup)
    bot.register_next_step_handler(message, clicker)


def clicker(message):
    get_weather(message)


@bot.message_handler(content_types=['text'])
def get_weather(message):
    """
    Функция, получающая и обрабатывающая информацию от API.
    Также запрашивает у пользователя конкретную информацию о погоде, интересующую его (посредством встроенных кнопок)
    Функция сохраняет информацию о погоде в базу данных users.bd
    с привязкой к информации о пользователе, сделавшем запрос.
    """

    city = message.text.strip().lower()
    weather_json = requests.get(
        f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_openweathermap}&units=metric')

    if weather_json.status_code == 200:

        data = json.loads(weather_json.text)

        json.dump(data, open("weather_from_API.json", 'w'))

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Температура за окном 🌡️', callback_data='temp'))
        markup.add(types.InlineKeyboardButton('Влажность 💦', callback_data='humid'))
        markup.add(types.InlineKeyboardButton('Сила ветра 🌪️', callback_data='wind'))
        markup.add(types.InlineKeyboardButton('Вся информация 👀', callback_data='all'))

        bot.reply_to(message, 'Какая именно информация тебя интересует? ', reply_markup=markup)

        conn = sqlite3.connect('./users.db', check_same_thread=False)
        cursor = conn.cursor()
        us_id = message.from_user.id
        us_name = message.from_user.first_name
        temp = data["main"]["temp"]
        temp_feels_like = data["main"]["feels_like"]
        humid = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        all_info = str(data)

        cursor.execute(
            'INSERT OR REPLACE INTO users (user_id, user_name, temp, temp_feels_like, humid, wind, all_info) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)', (us_id, us_name, temp, temp_feels_like, humid, wind, all_info))
        conn.commit()

        precipitation = data["weather"][0]["main"]

        if precipitation == 'Rain':
            precipitation_img = 'rain.gif'
        elif precipitation == 'Clouds':
            precipitation_img = 'clouds.gif'
        elif precipitation == 'Clear':
            precipitation_img = 'sunny.gif'
        elif precipitation == 'Thunderstorm':
            precipitation_img = 'thunderstorm.gif'
        elif precipitation == 'Snow':
            precipitation_img = 'snow.gif'
        else:
            precipitation_img = 'joke.jpg'

        image_file = open('Gif/' + precipitation_img, 'rb')
        bot.send_animation(message.chat.id, image_file)
        image_file.close()

    else:
        bot.send_message(message.chat.id, 'К сожалению такой город на планете Земля не найден, '
                                          'но не отчаивайся, попробуй ввести название города ещё раз '
                                          'или введи другой город.')


@bot.message_handler(content_types=['text'])
def get_temperature(message):
    """
    Функция для получения информации о температуре из БД users.bd
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Влажность 💦', callback_data='humid'))
    markup.add(types.InlineKeyboardButton('Сила ветра 🌪️', callback_data='wind'))
    markup.add(types.InlineKeyboardButton('Вся информация 👀', callback_data='all'))

    conn = sqlite3.connect('./users.db', check_same_thread=False)
    cursor = conn.cursor()

    us_id = message.chat.id

    cursor.execute(f'SELECT temp, temp_feels_like FROM users WHERE user_id ={us_id}')
    info = cursor.fetchall()
    conn.commit()
    cursor.close()

    bot.reply_to(message, f'Сейчас температура за окном: {info[0][0]} °C\n'
                          f'Ощущается как: {info[0][1]} °C\n')

    bot.send_message(message.chat.id, 'Что-нибудь ещё? ', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_humidity(message):
    """
    Функция для получения информации о влажности из БД users.bd
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Температура за окном 🌡️', callback_data='temp'))
    markup.add(types.InlineKeyboardButton('Сила ветра 🌪️', callback_data='wind'))
    markup.add(types.InlineKeyboardButton('Вся информация 👀', callback_data='all'))

    conn = sqlite3.connect('./users.db', check_same_thread=False)
    cursor = conn.cursor()

    us_id = message.chat.id

    cursor.execute(f'SELECT humid FROM users WHERE user_id ={us_id}')

    info = cursor.fetchall()

    conn.commit()
    cursor.close()
    bot.reply_to(message, f'Сейчас влажность: {info[0][0]}%\n')
    bot.send_message(message.chat.id, 'Что-нибудь ещё? ', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_wind(message):
    """
    Функция для получения информации о скорости ветра из БД users.bd
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Температура за окном 🌡️', callback_data='temp'))
    markup.add(types.InlineKeyboardButton('Влажность 💦', callback_data='humid'))
    markup.add(types.InlineKeyboardButton('Вся информация 👀', callback_data='all'))

    conn = sqlite3.connect('./users.db', check_same_thread=False)
    cursor = conn.cursor()

    us_id = message.chat.id

    cursor.execute(f'SELECT wind FROM users WHERE user_id ={us_id}')

    info = cursor.fetchall()

    conn.commit()
    cursor.close()
    bot.reply_to(message, f'Сейчас скорость ветра: {info[0][0]} м/с.\n')
    bot.send_message(message.chat.id, 'Что-нибудь ещё? ', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_all_info(message):
    """
    Функция для получения всей информации о погоде из БД users.bd
    """

    conn = sqlite3.connect('./users.db', check_same_thread=False)
    cursor = conn.cursor()

    us_id = message.chat.id

    cursor.execute(f'SELECT temp, temp_feels_like, humid, wind FROM users WHERE user_id ={us_id}')

    info = cursor.fetchall()

    conn.commit()
    cursor.close()
    bot.reply_to(message, f'Сейчас температура за окном: {info[0][0]} °C\n'
                          f'Ощущается как: {info[0][1]} °C\n\n'
                          f'Влажность: {info[0][2]}%\n'
                          f'Скорость ветра: {info[0][3]} м/с')
    bot.send_message(message.chat.id, 'Надеюсь, что погода не испортит тебе настроение! 🤔\n')


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    """ Кликер для встроенных кнопок"""

    if call.data == "temp":
        data = json.load(open("weather_from_API.json"))
        res = get_temperature(call.message)

    elif call.data == "humid":
        data = json.load(open("weather_from_API.json"))
        res = get_humidity(call.message)

    elif call.data == "wind":
        data = json.load(open("weather_from_API.json"))
        res = get_wind(call.message)

    elif call.data == "all":
        data = json.load(open("weather_from_API.json"))
        res = get_all_info(call.message)


bot.infinity_polling()
