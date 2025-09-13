import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from tender_api import ProZorroAPI
from config import TELEGRAM_TOKEN, CHAT_ID, CHECK_INTERVAL

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

api = ProZorroAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /start."""
    await update.message.reply_text("👋 Привіт! Це бот моніторингу тендерів ProZorro.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /help."""
    help_text = (
        "📖 Доступні команди:\n"
        "/start - початок роботи\n"
        "/help - довідка\n"
        "/tenders - отримати список нових тендерів"
    )
    await update.message.reply_text(help_text)

async def tenders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /tenders."""
    try:
        results = api.search_tenders()

        if not results:
            await update.message.reply_text("Немає нових тендерів.")
            return

        for tender in results[:5]:  # обмежимо вивід для зручності
            await update.message.reply_text(
                tender,
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Помилка у команді /tenders: {e}")
        await update.message.reply_text("⚠️ Сталася помилка при отриманні тендерів.")

async def auto_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Функція для автоматичної перевірки нових тендерів."""
    try:
        results = api.search_tenders()

        for tender in results:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=tender,
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Помилка авто-перевірки: {e}")

def main() -> None:
    """Головна функція запуску Telegram-бота."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Реєстрація команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tenders", tenders))

    # Запуск автоматичної перевірки кожні N секунд
    application.job_queue.run_repeating(auto_check, interval=CHECK_INTERVAL, first=10)

    logger.info("🚀 Бот запущено!")
    application.run_polling()

if __name__ == "__main__":
    main()