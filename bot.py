import logging
import json
import os
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Логирование
logging.basicConfig(level=logging.INFO)

# Этапы диалога
PHONE, LASTNAME = range(2)

# Подключение к Google Таблицам
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDS")
    creds_dict = json.loads(creds_json)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open("clients").sheet1
    return sheet

# Старт диалога
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напишите номер телефона клиента для предоставления дополнительного бортового депозита")
    return PHONE

# Получаем номер телефона
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Теперь напишите фамилию клиента")
    return LASTNAME

# Получаем фамилию и сохраняем в таблицу
async def get_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = context.user_data.get("phone")
    lastname = update.message.text
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        sheet = get_gsheet()
        sheet.append_row([date, phone, lastname])
        await update.message.reply_text("Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, который клиент может получить при бронировании круиза в следующие 48 часов.")
    except Exception as e:
        logging.error(f"Ошибка при записи в таблицу: {e}")
        await update.message.reply_text("Ошибка при сохранении данных, попробуйте позже.")
    return ConversationHandler.END

# Прерывание диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Основной запуск
def main():
    token = os.environ["TOKEN"]
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lastname)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
