# Конфігурація бота
import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()

# Telegram Bot налаштування
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не встановлено в .env файлі")
if not CHAT_ID:
    raise ValueError("CHAT_ID не встановлено в .env файлі")

# Налаштування ProZorro API
BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"

# CPV коди для пошуку (будівництво та ремонт)
CPV_CODES = [
    "15420000", "15330000", "15320000", "15610000", "15620000", "15810000", 
    "15820000", "15830000", "15840000", "15850000", "15860000", "15870000", 
    "15980000"
]

# Регіони для фільтрації тендерів
ALLOWED_REGIONS = ["Київська", "Черкаська", "м. Київ", "Київська область", "Черкаська область"]
ALLOWED_REGION_KEYWORDS = ["Київ", "Черка"]

# HTTP заголовки для запитів
SESSION_HEADERS = {"User-Agent": "pedchenko-tender-bot/1.0 (contact: example@example.com)"}

# Налаштування пагінації (кількість тендерів на сторінку)
PAGE_LIMIT = 100
MAX_PAGES = 15

# Налаштування бота
CHECK_INTERVAL = 600  # 10 хвилин (інтервал автоматичної перевірки)
REQUEST_TIMEOUT = 3   # секунди (таймаут запитів)
REQUEST_DELAY = 0.1   # секунди (затримка між запитами)
