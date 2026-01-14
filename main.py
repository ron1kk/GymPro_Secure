import telebot
from telebot import types, apihelper
from gtts import gTTS
import os
import sqlite3
from threading import Lock, Thread
import time
from dotenv import load_dotenv

# --- ИНИЦИАЛИЗАЦИЯ ---
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1245117074
ADMIN_NICK = "@Dbebrreuf"

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    exit()

# Настройки для Railway (БЕЗ ПРОКСИ)
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=50)
db_lock = Lock()
user_data = {}

if not os.path.exists('voice_cache'):
    os.makedirs('voice_cache')

# --- БД ---
def init_db():
    with db_lock:
        conn = sqlite3.connect('gym_pro_users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return conn, cursor

conn, cursor = init_db()

# --- КОНТЕНТ (Я ВЕРНУЛ ТВОИ СПИСКИ) ---
WORKOUTS = {
    "ВЕРХ ТЕЛА": [
        {"name": "Классические отжимания", "reps": "3 x 15", "desc": "Грудь почти касается пола, тело ровное."},
        {"name": "Обратные отжимания", "reps": "3 x 12", "desc": "Руки на опоре сзади, локти назад."},
        {"name": "Широкие отжимания", "reps": "3 x 12", "desc": "Руки шире плеч для проработки груди."},
        {"name": "Алмазные отжимания", "reps": "3 x 10", "desc": "Ладони близко, образуют ромб."},
        {"name": "Планка на локтях", "reps": "3 x 45 сек", "desc": "Классическая планка."}
    ],
    "НОГИ И ЯГОДИЦЫ": [
        {"name": "Приседания", "reps": "4 x 20", "desc": "Пятки на полу, таз назад."},
        {"name": "Классические выпады", "reps": "3 x 12", "desc": "Колено сзади почти до пола."},
        {"name": "Боковые выпады", "reps": "3 x 15", "desc": "Шаг в сторону, спина прямая."},
        {"name": "Ягодичный мостик", "reps": "3 x 20", "desc": "Выталкиваем таз вверх."},
        {"name": "Подъемы на носки", "reps": "3 x 25", "desc": "Максимальный подъем вверх."}
    ]
}

# ВАЖНО: Вставь сюда свои полные PRO_DIET и PRO_WORK из старого кода!
PRO_DIET = {1: "🍏 День 1: Овсянка + яйца. Обед: Курица + Гречка. Ужим: Творог.", 2: "🍏 День 2: Омлет. Обед: Рыба + Рис. Ужин: Салат с тунцом."}
PRO_WORK = {1: "💪 День 1: 50 приседаний, 30 отжиманий, 2 мин планки.", 2: "💪 День 2: 40 выпадов, 20 обратных отжиманий, 50 пресс."}

# --- ФУНКЦИИ ИИ (ОЗВУЧКА) ---
def pre_generate_voices():
    print("🎙 ИИ генерирует озвучку...")
    for cat in WORKOUTS:
        for ex in WORKOUTS[cat]:
            safe_name = "".join([c for c in ex['name'] if c.isalnum()])
            path = f"voice_cache/{safe_name}.mp3"
            if not os.path.exists(path):
                try:
                    tts = gTTS(text=f"{ex['name']}. Цель {ex['reps']}", lang='ru')
                    tts.save(path)
                except: pass

def init_user(uid):
    if uid not in user_data:
        user_data[uid] = {'plan': [], 'idx': 0}
    return user_data[uid]

def get_main_kb():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("ВЕРХ ТЕЛА", "НОГИ И ЯГОДИЦЫ")
    m.row("🔥 ПРЕМІУМ КУРС (120 грн)")
    m.row("🥗 ГАЙД ПО ПИТАНИЮ")
    m.row("☕️ ПОДДЕРЖАТЬ АВТОРА")
    return m

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    with db_lock:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)',
                       (uid, message.from_user.username, message.from_user.first_name))
        conn.commit()
    init_user(uid)
    bot.send_message(message.chat.id, "🚀 Бот GYM PRO готов!", reply_markup=get_main_kb())

def send_exercise(chat_id, uid):
    data = user_data.get(uid)
    if not data or data['idx'] >= len(data['plan']):
        bot.send_message(chat_id, "🎉 Тренировка окончена!", reply_markup=get_main_kb())
        return
    ex = data['plan'][data['idx']]

    # ОЗВУЧКА ИИ
    def handle_voice():
        safe_name = "".join([c for c in ex['name'] if c.isalnum()])
        path = f"voice_cache/{safe_name}.mp3"
        if os.path.exists(path):
            with open(path, 'rb') as v: 
                bot.send_voice(chat_id, v)

    Thread(target=handle_voice).start()
    
    caption = f"🔥 *{ex['name']}*\n🎯 {ex['reps']}\n\n📝 {ex['desc']}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ ДАЛЬШЕ", callback_data="next_step"))
    bot.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "next_step")
def next_step(call):
    uid = call.from_user.id
    if uid in user_data:
        user_data[uid]['idx'] += 1
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_exercise(call.message.chat.id, uid)

@bot.message_handler(func=lambda message: message.text == "🔥 ПРЕМІУМ КУРС (120 грн)")
def premium_menu(message):
    uid = message.from_user.id
    with sqlite3.connect('gym_pro_users.db') as c:
        res = c.execute('SELECT is_premium FROM users WHERE user_id = ?', (uid,)).fetchone()

    if res and res[0] == 1:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🏃‍♂️ ТРЕНУВАННЯ (50 ДНІВ)", "🍏 ХАРЧУВАННЯ (30 ДНІВ)")
        markup.add("☕️ ПОДДЕРЖАТЬ АВТОРА", "⬅️ НАЗАД")
        bot.send_message(message.chat.id, "🌟 Твой Премиум-кабинет!", reply_markup=markup)
    else:
        info_text = (
            "🚀 **ПРЕМІУМ КУРС: ТРАНСФОРМАЦІЯ**\n\n"
            "💳 **Оплата на карту:**\n`4102321251250550`\n\n"
            "📸 **ПРИШЛИ СКРИНШОТ ОПЛАТЫ СЮДА**\n"
            f"Ваш ID: `{uid}`"
        )
        bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "☕️ ПОДДЕРЖАТЬ АВТОРА")
def support_author(message):
    bot.send_message(message.chat.id, "☕️ **ПОДДЕРЖКА ПРОЕКТА**\n\n💳 Карта: `4102321251250550`", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment(message):
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ ВЫДАТЬ ПРЕМ", callback_data=f"adm_give_{uid}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💰 ЧЕК от {uid}", reply_markup=markup)
    bot.reply_to(message, "⏳ Чек отправлен на проверку!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_give_"))
def admin_action(call):
    if call.from_user.id != ADMIN_ID: return
    target_id = int(call.data.split("_")[2])
    with sqlite3.connect('gym_pro_users.db') as c:
        c.execute('UPDATE users SET is_premium = 1 WHERE user_id = ?', (target_id,))
        c.commit()
    bot.send_message(target_id, "🎉 ПРЕМИУМ АКТИВИРОВАН!")
    bot.answer_callback_query(call.id, "Готово!")

@bot.message_handler(func=lambda message: message.text == "🏃‍♂️ ТРЕНУВАННЯ (50 ДНІВ)")
def prem_work(message):
    uid = message.from_user.id
    with sqlite3.connect('gym_pro_users.db') as c:
        res = c.execute('SELECT is_premium FROM users WHERE user_id = ?', (uid,)).fetchone()
    if res and res[0] == 1:
        for i in range(1, 51, 10):
            chunk = "\n\n".join([PRO_WORK.get(j, f"День {j}") for j in range(i, min(i+10, 51))])
            bot.send_message(message.chat.id, chunk)
    else: bot.send_message(message.chat.id, "🔒 Купите Премиум.")

@bot.message_handler(func=lambda message: message.text == "🍏 ХАРЧУВАННЯ (30 ДНІВ)")
def prem_nutr(message):
    uid = message.from_user.id
    with sqlite3.connect('gym_pro_users.db') as c:
        res = c.execute('SELECT is_premium FROM users WHERE user_id = ?', (uid,)).fetchone()
    if res and res[0] == 1:
        for i in range(1, 31, 10):
            chunk = "\n\n".join([PRO_DIET.get(j, f"День {j}") for j in range(i, min(i+10, 31))])
            bot.send_message(message.chat.id, chunk)
    else: bot.send_message(message.chat.id, "🔒 Купите Премиум.")

@bot.message_handler(func=lambda message: message.text in WORKOUTS.keys())
def start_w(message):
    uid = message.from_user.id
    d = init_user(uid)
    d['plan'], d['idx'] = WORKOUTS[message.text], 0
    send_exercise(message.chat.id, uid)

@bot.message_handler(func=lambda message: message.text == "⬅️ НАЗАД")
def back(message): start(message)

if __name__ == "__main__":
    pre_generate_voices()
    print("🚀 БОТ ЗАПУЩЕН!")
    bot.infinity_polling(timeout=10)
