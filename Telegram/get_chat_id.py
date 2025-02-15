import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, MessageHandler


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global latest_message
    await update.message.reply_text(f"Chat ID: {update.message.chat.id}")
    print(f"Chat ID for {update.message.chat.full_name} is {update.message.chat.id}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Error occurred: {context.error}')

def main():
    token = os.environ.get("telegram_api_key")  # get token from env
    if not token:
        raise ValueError("Missing telegram_api_key environment variable")
    app = ApplicationBuilder().token(token).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)
    
    # Start bot
    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()