import os
import csv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

PHONE, SURNAME = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напишите номер телефона клиента для предоставления дополнительного бортового депозита")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Теперь напишите фамилию клиента")
    return SURNAME

async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    surname = update.message.text
    phone = context.user_data['phone']

    # Сохраняем в CSV-файл
    with open("clients.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([phone, surname])

    await update.message.reply_text(
        "Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, "
        "который клиент может получить при бронировании круиза в следующие 48 часов."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.run_polling()
