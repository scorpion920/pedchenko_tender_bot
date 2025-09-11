import logging
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from tender_api import ProZorroAPI
from config import TELEGRAM_TOKEN, CHAT_ID, CHECK_INTERVAL

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

api = ProZorroAPI()


def start(update: Update, context: CallbackContext) -> None:
    """
    Обробник команди /start.
    Відправляє вітальне повідомлення користувачу.

    Args:
        update (Update): Об'єкт Telegram Update.
        context (CallbackContext): Контекст виконання.
    """
    update.message.reply_text("👋 Привіт! Це бот моніторингу тендерів ProZorro.")


def help_command(update: Update, context: CallbackContext) -> None:
    """
    Обробник команди /help.
    Пояснює доступні команди.

    Args:
        update (Update): Об'єкт Telegram Update.
        context (CallbackContext): Контекст виконання.
    """
    help_text = (
        "📖 Доступні команди:\n"
        "/start - початок роботи\n"
        "/help - довідка\n"
        "/tenders - отримати список нових тендерів"
    )
    update.message.reply_text(help_text)


def tenders(update: Update, context: CallbackContext) -> None:
    """
    Обробник команди /tenders.
    Виконує пошук нових тендерів і надсилає користувачу.

    Args:
        update (Update): Об'єкт Telegram Update.
        context (CallbackContext): Контекст виконання.
    """
    try:
        results = api.search_tenders()

        if not results:
            update.message.reply_text("Немає нових тендерів.")
            return

        for tender in results[:5]:  # обмежимо вивід для зручності
            message = (
                f"📌 {tender['title']}\n"
                f"ID: {tender['tenderID']}\n"
                f"Статус: {tender['status']}\n"
                f"Регіон: {tender['region']}\n"
                f"Дата: {tender['dateModified']}\n"
                f"https://prozorro.gov.ua/tender/{tender['id']}"
            )
            update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Помилка у команді /tenders: {e}")
        update.message.reply_text("⚠️ Сталася помилка при отриманні тендерів.")


def auto_check(context: CallbackContext) -> None:
    """
    Функція для автоматичної перевірки нових тендерів.
    Виконується за розкладом кожні N секунд.

    Args:
        context (CallbackContext): Контекст виконання.
    """
    try:
        results = api.search_tenders()

        for tender in results:
            message = (
                f"📌 {tender['title']}\n"
                f"ID: {tender['tenderID']}\n"
                f"Статус: {tender['status']}\n"
                f"Регіон: {tender['region']}\n"
                f"Дата: {tender['dateModified']}\n"
                f"https://prozorro.gov.ua/tender/{tender['id']}"
            )
            context.bot.send_message(chat_id=CHAT_ID, text=message)

    except Exception as e:
        logger.error(f"Помилка авто-перевірки: {e}")


def main() -> None:
    """
    Головна функція запуску Telegram-бота.
    """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Реєстрація команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("tenders", tenders))

    # Запуск автоматичної перевірки кожні N секунд
    job_queue = updater.job_queue
    job_queue.run_repeating(auto_check, interval=CHECK_INTERVAL, first=10)

    logger.info("🚀 Бот запущено!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
