import os
import json
import logging
from datetime import datetime
from flask import Flask, request

import telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

ASK_PHONE, ASK_NAME = range(2)
logging.basicConfig(level=logging.INFO)

# Flask для Webhook
app = Flask(__name__)

# Инициализация Telegram API
BOT_TOKEN = os.getenv("TOKEN")
bot = telegram.Bot(BOT_TOKEN)

# Google Sheets setup
def authorize_google_sheets():
    creds_json = os.environ.get("GOOGLE_CREDS")
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("clients").sheet1

# Хранилище состояния
user_state = {}

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    app.dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Бот работает!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = {"step": 1}
    await context.bot.send_message(chat_id=chat_id, text="Напишите номер телефона клиента для предоставления дополнительного бортового депозита.")
    return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_state:
        user_state[chat_id] = {"step": 1}
        await context.bot.send_message(chat_id=chat_id, text="Напишите номер телефона клиента.")
        return

    state = user_state[chat_id]

    if state["step"] == 1:
        state["phone"] = text
        state["step"] = 2
        await context.bot.send_message(chat_id=chat_id, text="Теперь напишите фамилию клиента.")
    elif state["step"] == 2:
        state["surname"] = text
        try:
            sheet = authorize_google_sheets()
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                state["phone"],
                state["surname"]
            ])
            await context.bot.send_message(chat_id=chat_id,
                text="Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, который клиент может получить при бронировании круиза в следующие 48 часов.")
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Ошибка: {e}")
        user_state.pop(chat_id, None)

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.dispatcher = application
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    )
