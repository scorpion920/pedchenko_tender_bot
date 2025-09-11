"""
Telegram бот для моніторингу тендерів ProZorro
"""
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue

from config import TELEGRAM_TOKEN, CHAT_ID, CHECK_INTERVAL
from tender_api import ProZorroAPI


class TenderBot:
    """Клас Telegram бота для моніторингу тендерів"""
    
    def __init__(self):
        self.api = ProZorroAPI()
        self.sent_tenders = set()  # Зберігаємо вже надіслані tender_id
    
    def start_command(self, update: Update, context: CallbackContext):
        """Команда /start"""
        welcome_message = (
            "🚀 Ласкаво просимо до бота моніторингу тендерів ProZorro!\n\n"
            "📋 Доступні команди:\n"
            "/tenders - Знайти актуальні тендери\n"
            "/help - Показати довідку\n\n"
            "🤖 Бот автоматично перевіряє нові тендери кожні 10 хвилин"
        )
        update.message.reply_text(welcome_message)
    
    def help_command(self, update: Update, context: CallbackContext):
        """Команда /help"""
        help_message = (
            "📖 Довідка по боту:\n\n"
            "🔍 Фільтри пошуку:\n"
            "• Статус: active.tendering (прийом пропозицій)\n"
            "• Регіони: Київ, Черкаси\n"
            "• CPV коди: будівництво та ремонт (1542xxx-1598xxx)\n\n"
            "⚙️ Команди:\n"
            "/tenders - Ручний пошук тендерів\n"
            "/start - Головне меню\n\n"
            "🔄 Автоматичні сповіщення надходять кожні 10 хвилин"
        )
        update.message.reply_text(help_message)
    
    def tenders_command(self, update: Update, context: CallbackContext):
        """Команда /tenders - ручний пошук тендерів"""
        try:
            update.message.reply_text("🔄 Шукаю актуальні тендери...")
            
            messages = self.api.search_tenders()
            
            if not messages:
                update.message.reply_text("❌ Нових тендерів за заданими фільтрами не знайдено.")
                return
            
            # Відправляємо кожен тендер окремим повідомленням
            for message in messages:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=message
                )
                time.sleep(0.2)  # Невелика затримка між повідомленнями
                
            update.message.reply_text(f"✅ Знайдено {len(messages)} тендерів!")
            
        except Exception as e:
            update.message.reply_text(f"❌ Помилка: {e}")
    
    def periodic_check(self, context: CallbackContext):
        """Періодична перевірка нових тендерів"""
        try:
            print("🔄 Виконую періодичну перевірку тендерів...")
            
            messages = self.api.search_tenders()
            
            if messages:
                for message in messages:
                    context.bot.send_message(chat_id=CHAT_ID, text=message)
                    time.sleep(0.2)
                
                print(f"✅ Відправлено {len(messages)} нових тендерів")
            else:
                print("ℹ️ Нових тендерів не знайдено")
                
        except Exception as e:
            print(f"❌ Помилка в періодичній перевірці: {e}")
    
    def run(self):
        """Запуск бота"""
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        jq: JobQueue = updater.job_queue

        # Регистрация команд
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("tenders", self.tenders_command))

        # Автоматическая проверка каждые 10 минут
        jq.run_repeating(self.periodic_check, interval=CHECK_INTERVAL, first=10)

        print("🤖 Бот запущено!")
        print("📋 Доступні команди: /start, /help, /tenders")
        print(f"⏰ Автоматична перевірка кожні {CHECK_INTERVAL//60} хвилин")
        
        updater.start_polling()
        updater.idle()


if __name__ == "__main__":
    bot = TenderBot()
    bot.run()
