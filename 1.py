from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
import time
import requests
from datetime import datetime
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------------
# Налаштування
# -------------------------------
TELEGRAM_TOKEN = "8233329358:AAEdJ2_qfvu9at-xGCRMEcGAgzRq28FHhBs"  # встав свій токен
CHAT_ID = 1423587664  # твій Telegram ID або групи

BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"
CPV_CODES = ["15420000", "15330000", "15320000", "15610000", "15620000",
             "15810000", "15820000", "15830000", "15840000", "15850000",
             "15860000", "15870000", "15980000"]
ALLOWED_REGIONS = ["Київська", "Черкаська"]
ALLOWED_REGION_KEYWORDS = ["Київ", "Черка"]
SESSION_HEADERS = {"User-Agent": "pedchenko-tender-bot/1.0 (contact: example@example.com)"}

PAGE_LIMIT = 50
MAX_PAGES = 3
CHECK_INTERVAL = 600  # 10 хвилин

sent_tenders = set()  # зберігати вже надіслані tender_id

# -------------------------------
# Налаштування сесії
# -------------------------------
def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET"], raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(SESSION_HEADERS)
    return session

SESSION = create_session()

# -------------------------------
# Функції для тендерів
# -------------------------------
def get_tenders(limit=PAGE_LIMIT):
    try:
        response = SESSION.get(BASE_URL, params={"limit": limit, "descending": 1}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Помилка отримання тендерів: {e}")
        return {}

def get_tender_details(tender_id):
    try:
        url = f"{BASE_URL}/{tender_id}"
        response = SESSION.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.RequestException as e:
        print(f"Помилка отримання деталей тендера {tender_id}: {e}")
        return {}

# -------------------------------
# Формування повідомлення
# -------------------------------
def format_tender_message(details):
    items = details.get('items', []) or []
    raw_cpvs: List[str] = list({(item.get('classification', {}) or {}).get('id', '') for item in items if item.get('classification')})
    item_cpvs = [cpv.split('-')[0] if isinstance(cpv, str) else '' for cpv in raw_cpvs]

    tender_period = details.get('tenderPeriod', {}) or {}
    deadline_str = tender_period.get('endDate', None)
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M")
        except Exception:
            deadline = deadline_str
    else:
        deadline = "Немає дедлайну"

    procuring_entity = details.get('procuringEntity', {}) or {}
    edrpou = (procuring_entity.get('identifier', {}) or {}).get('id', 'Немає ЄДРПОУ')
    tender_url = f"https://prozorro.gov.ua/tender/{details.get('id')}"

    message = f"📌 Новий тендер!\n" \
              f"Tender ID: {details.get('id')}\n" \
              f"Предмет закупівлі: {details.get('title', 'Немає назви')}\n" \
              f"CPV Код: {', '.join(item_cpvs)}\n" \
              f"Статус: {details.get('status', 'Немає статусу')}\n" \
              f"Дедлайн: {deadline}\n" \
              f"Замовник: {procuring_entity.get('name', 'Немає замовника')}\n" \
              f"ЄДРПОУ: {edrpou}\n" \
              f"Сума: {details.get('value', {}).get('amount', 'немає бюджету')} {details.get('value', {}).get('currency', '')}\n" \
              f"Посилання: {tender_url}"
    return message

# -------------------------------
# Основна логіка фільтру
# -------------------------------
def fetch_tenders():
    first_page = get_tenders(limit=PAGE_LIMIT)
    if not first_page or not first_page.get('data'):
        return []

    next_offset = (first_page.get('next_page') or {}).get('offset')
    tenders_pages = [first_page.get('data', [])]

    for _ in range(MAX_PAGES - 1):
        if not next_offset:
            break
        try:
            page = SESSION.get(BASE_URL, params={"limit": PAGE_LIMIT, "descending": 1, "offset": next_offset}, timeout=15)
            page.raise_for_status()
            page_json = page.json()
            tenders_pages.append(page_json.get('data', []))
            next_offset = (page_json.get('next_page') or {}).get('offset')
        except Exception:
            break

    results = []
    for tenders in tenders_pages:
        for tender in tenders:
            tender_id = tender.get('id')
            if not tender_id or tender_id in sent_tenders:
                continue

            details = get_tender_details(tender_id)
            if not details:
                continue

            if details.get('status') != "active.tendering":
                continue

            items = details.get('items', []) or []
            raw_cpvs: List[str] = list({(item.get('classification', {}) or {}).get('id', '') for item in items if item.get('classification')})
            item_cpvs = [cpv.split('-')[0] if isinstance(cpv, str) else '' for cpv in raw_cpvs]
            matches_cpv = any((cpv or '').startswith(code) for cpv in item_cpvs for code in CPV_CODES)
            if not matches_cpv:
                continue

            procuring_entity = details.get('procuringEntity', {}) or {}
            region = (procuring_entity.get('address', {}) or {}).get('region', '')
            if not (region in ALLOWED_REGIONS or any(kw in region for kw in ALLOWED_REGION_KEYWORDS)):
                continue

            sent_tenders.add(tender_id)
            results.append(details)

    return results

# -------------------------------
# Telegram-команда /tenders
# -------------------------------
def tenders_command(update: Update, context: CallbackContext):
    bot = context.bot
    try:
        update.message.reply_text("🔄 Шукаю актуальні тендери...")
        tenders = fetch_tenders()
        if not tenders:
            update.message.reply_text("Немає нових тендерів за поточними фільтрами.")
            return
        for t in tenders:
            bot.send_message(chat_id=update.effective_chat.id, text=format_tender_message(t))
            time.sleep(0.2)
    except Exception as e:
        update.message.reply_text(f"Помилка: {e}")

# -------------------------------
# Функція автоматичної перевірки
# -------------------------------
def periodic_check(context: CallbackContext):
    bot = context.bot
    try:
        tenders = fetch_tenders()
        for t in tenders:
            bot.send_message(chat_id=CHAT_ID, text=format_tender_message(t))
            time.sleep(0.2)
    except Exception as e:
        print(f"Periodic check error: {e}")

# -------------------------------
# Запуск бота
# -------------------------------
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    jq: JobQueue = updater.job_queue

    # Команда /tenders
    dp.add_handler(CommandHandler("tenders", tenders_command))

    # Автооновлення раз на 10 хв
    jq.run_repeating(periodic_check, interval=CHECK_INTERVAL, first=10)

    print("Бот запущено. Використай команду /tenders для перевірки актуальних тендерів.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
