import telebot
from telebot import types
import sqlite3
from gtts import gTTS
import os

# Твой токен, который мы вчера использовали
TOKEN = "7963959960:AAH2t1qg_6W7Fp7oI28f0LOnO-0x-V3hL80"

bot = telebot.TeleBot(TOKEN)

# --- ЛОГИКА БАЗЫ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('gym_pro.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS progress 
                      (user_id INTEGER, exercise TEXT, reps INTEGER)''')
    conn.commit()
    conn.close()

# --- КОМАНДЫ БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    init_db() # Создаем базу при первом запуске
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Начать тренировку")
    btn2 = types.KeyboardButton("Статистика")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, "1 Января! Время разрывать мир. Погнали?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Начать тренировку")
def training(message):
    # 1. Озвучка
    text_to_say = "Первое упражнение: приседания, 15 повторений"
    tts = gTTS(text=text_to_say, lang='ru')
    tts.save("workout.mp3")
    
    with open("workout.mp3", 'rb') as audio:
        bot.send_voice(message.chat.id, audio)
    
    # 2. Картинка (с проверкой, чтобы бот не вылетел без папки images)
    try:
        with open('images/leg1.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="Делай красиво!")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "🏋️‍♂️ Текст упражнения: Приседания (15 раз). Картинки пока нет.")

    # 3. Сохранение в базу
    conn = sqlite3.connect('gym_pro.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO progress VALUES (?, ?, ?)", (message.from_user.id, "Приседания", 15))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)