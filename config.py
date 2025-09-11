"""
config.py — модуль конфігурації для Telegram-бота моніторингу ProZorro.

Цей файл завантажує налаштування з .env файлу або змінних середовища,
перевіряє їх валідність та надає константи для використання в інших модулях.
"""

import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()


def get_env_variable(name: str, cast_type=str, required: bool = True):
    """
    Отримати змінну середовища з .env файлу.

    Args:
        name (str): назва змінної середовища
        cast_type (type): тип даних, у який потрібно привести (str, int і т.д.)
        required (bool): чи обов’язкова змінна

    Returns:
        будь-який тип: значення змінної

    Raises:
        ValueError: якщо змінну не знайдено і вона обов'язкова
    """
    value = os.getenv(name)

    if value is None:
        if required:
            raise ValueError(f"⚠️ Обов'язкова змінна середовища {name} відсутня у .env файлі")
        return None

    try:
        return cast_type(value)
    except Exception:
        raise ValueError(f"⚠️ Змінна {name} повинна бути типу {cast_type.__name__}")


# --- Telegram Bot ---
TELEGRAM_TOKEN = get_env_variable("TELEGRAM_TOKEN", str, required=True)
CHAT_ID = get_env_variable("CHAT_ID", int, required=True)

# --- ProZorro API ---
BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"

# CPV коди для пошуку (харчування та товари)
CPV_CODES = [
    "15420000", "15330000", "15320000", "15610000", "15620000", "15810000",
    "15820000", "15830000", "15840000", "15850000", "15860000", "15870000",
    "15980000"
]

# Регіони для фільтрації тендерів
ALLOWED_REGIONS = [
    "Київська", "Черкаська", "м. Київ", "Київська область", "Черкаська область"
]
ALLOWED_REGION_KEYWORDS = ["Київ", "Черка"]

# HTTP заголовки для запитів
SESSION_HEADERS = {
    "User-Agent": "pedchenko-tender-bot/1.0 (contact: example@example.com)"
}

# --- Параметри API ---
PAGE_LIMIT = 100   # кількість тендерів на сторінку
MAX_PAGES = 15     # максимум сторінок для обходу

# --- Налаштування бота ---
CHECK_INTERVAL = 600  # 10 хвилин (інтервал авто-перевірки)
REQUEST_TIMEOUT = 3   # секунди (таймаут запитів)
REQUEST_DELAY = 0.1   # секунди (затримка між запитами)
