from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Храним состояние каждого пользователя
user_state = {}

TOKEN = "7542302190:AAHPUDMKzwdjJRLq0H7SRrhh8fkUTOFK5_8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = {"step": 1}
    await context.bot.send_message(chat_id=chat_id, text="Напишите номер телефона клиента для предоставления дополнительного бортового депозита")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    state = user_state.get(chat_id, {"step": 1})

    if state["step"] == 1:
        state["phone"] = text
        state["step"] = 2
        await context.bot.send_message(chat_id=chat_id, text="Теперь напишите фамилию клиента")
    elif state["step"] == 2:
        state["surname"] = text
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Спасибо! К номеру телефона клиента привязан дополнительный бортовой депозит в размере 5000 руб, который клиент может получить при бронировании круиза в следующие 48 часов."
        )
        user_state[chat_id] = {"step": 1}
    else:
        await context.bot.send_message(chat_id=chat_id, text="Введите команду /start")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    app.run_polling()
