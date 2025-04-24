import logging
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("clients").sheet1  # Название таблицы

# --- Telegram Setup ---
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '7542302190:AAHPUDMKzwdjJRLq0H7SRrhh8fkUTOFK5_8'
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_state[chat_id] = {"step": 1}
    await context.bot.send_message(chat_id=chat_id, text="Напишите номер телефона клиента для предоставления дополнительного бортового депозита")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    if chat_id not in user_state:
        await start(update, context)
        return

    state = user_state[chat_id]

    if state["step"] == 1:
        state["phone"] = text
        state["step"] = 2
        await context.bot.send_message(chat_id=chat_id, text="Теперь напишите фамилию клиента")
    elif state["step"] == 2:
        state["surname"] = text
        state["step"] = 0
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Сохраняем в таблицу
        sheet.append_row([date, state["phone"], state["surname"]])

        await context.bot.send_message(chat_id=chat_id,
            text="Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, который клиент может получить при бронировании круиза в следующие 48 часов.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_webhook(
    listen="0.0.0.0",
    port=10000,
    url_path=BOT_TOKEN,
    webhook_url=f"https://telegram-cruise-bot.onrender.com/{BOT_TOKEN}"
)
