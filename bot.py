from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, CallbackContext
import os

TOKEN = os.environ.get("TOKEN")

app = Flask(__name__)
bot = Bot(token=TOKEN)

dispatcher = Dispatcher(bot=bot, update_queue=None)

user_state = {}

def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_state[chat_id] = {"step": 1}
    context.bot.send_message(chat_id=chat_id, text="Напишите номер телефона клиента для предоставления дополнительного бортового депозита")

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_state.get(chat_id, {"step": 0})

    if state["step"] == 1:
        state["phone"] = text
        state["step"] = 2
        context.bot.send_message(chat_id=chat_id, text="Теперь напишите фамилию клиента")
    elif state["step"] == 2:
        state["surname"] = text
        context.bot.send_message(chat_id=chat_id,
            text=f"Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, который клиент может получить при бронировании круиза в следующие 48 часов.")
        state["step"] = 0
    user_state[chat_id] = state

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Бот запущен!"

if __name__ == "__main__":
    app.run(port=8080)
