import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from telegram.ext.filters import TEXT, COMMAND

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояние каждого пользователя (номер шага, введённый телефон и фамилия)
user_state = {}

# Стартовая команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"step": 1}
    await update.message.reply_text("Напишите номер телефона клиента для предоставления дополнительного бортового депозита")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    if user_id not in user_state:
        user_state[user_id] = {"step": 1}
        await update.message.reply_text("Напишите номер телефона клиента для предоставления дополнительного бортового депозита")
        return

    state = user_state[user_id]

    if state["step"] == 1:
        state["phone"] = message_text
        state["step"] = 2
        await update.message.reply_text("Теперь напишите фамилию клиента")
    elif state["step"] == 2:
        state["surname"] = message_text
        await update.message.reply_text(
            f"Спасибо! К номеру {state['phone']} привязан дополнительный бортовой депозит в размере 5000 руб, "
            f"который клиент может получить при бронировании круиза в следующие 48 часов."
        )
        user_state.pop(user_id)  # Сброс состояния

# Токен будет подставлен автоматически через переменные окружения
import os
TOKEN = os.getenv("TOKEN")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(TEXT & ~COMMAND, handle_message))

    app.run_polling()
