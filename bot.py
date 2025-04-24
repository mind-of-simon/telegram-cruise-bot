import os
import json
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", 10000))
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

user_state = {}

# Авторизация в Google Sheets
def authorize_google_sheets():
    creds_json = os.getenv("GOOGLE_CREDS")
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("clients").sheet1

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = {"step": 1}
    await update.message.reply_text("Укажите последние 6 цифр номера телефона клиента для предоставления дополнительного бортового депозита.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_state.get(chat_id, {"step": 1})

   if state["step"] == 1:
    digits = ''.join(c for c in text if c.isdigit())
    if len(digits) < 6:
        await update.message.reply_text("Необходимо ввести не менее 6 цифр номера телефона. Попробуйте ещё раз.")
        return
    state["phone"] = text
    state["step"] = 2
    user_state[chat_id] = state
    await update.message.reply_text("Теперь напишите фамилию клиента.")

    elif state["step"] == 2:
        state["surname"] = text
        try:
            sheet = authorize_google_sheets()
            date = datetime.now(timezone(timedelta(hours=3))).strftime('%Y-%m-%d %H:%M')
            sheet.append_row([
                date,
                state["phone"],
                state["surname"]
            ])
            await update.message.reply_text("Спасибо! Депозит 5000 руб активирован. Действует 48 часов.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
        user_state.pop(chat_id, None)

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{RENDER_HOSTNAME}/{BOT_TOKEN}"
    )
