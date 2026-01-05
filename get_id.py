import telebot

TOKEN = "8528053486:AAFzfW8NP0NJQSKztNlNz8TGGJy9BbRQOaE"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def get_file_id(message):
    # Берем ID самой большой версии фото
    file_id = message.photo[-1].file_id
    bot.reply_to(message, f"File ID этой картинки:\n`{file_id}`", parse_mode="Markdown")

print("Бот запущен. Скидывай ему фото, чтобы получить их ID!")
bot.polling()