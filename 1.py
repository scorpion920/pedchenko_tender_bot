import requests
import time
from typing import List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

print("🚀 Скрипт стартував!")

BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"

CPV_CODES = [
    "15420000", "15330000", "15320000", "15610000", "15620000", "15810000", 
    "15820000", "15830000", "15840000", "15850000", "15860000", "15870000", 
    "15980000"
]

ALLOWED_REGIONS = ["Київська", "Черкаська"]

SESSION_HEADERS = {"User-Agent": "pedchenko-tender-bot/1.0 (contact: example@example.com)"}

MAX_PAGES = 8
PAGE_LIMIT = 200

def create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(SESSION_HEADERS)
    return session

SESSION = create_session()

def get_tenders(limit=20):
    try:
        response = SESSION.get(
            BASE_URL,
            params={"limit": limit, "descending": 1},
            timeout=15,
        )
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

first_page = get_tenders(limit=PAGE_LIMIT)

if not first_page or not first_page.get('data'):
    print("Тендери не знайдені.")
else:
    max_pages = MAX_PAGES
    next_offset = (first_page.get('next_page') or {}).get('offset')
    tenders_pages = [first_page.get('data', [])]
    
    for _ in range(max_pages - 1):
        if not next_offset:
            break
        try:
            page = SESSION.get(
                BASE_URL,
                params={"limit": PAGE_LIMIT, "descending": 1, "offset": next_offset},
                timeout=15,
            )
            page.raise_for_status()
            page_json = page.json()
            tenders_pages.append(page_json.get('data', []))
            next_offset = (page_json.get('next_page') or {}).get('offset')
        except Exception:
            break

    matches_found = 0
    for tenders in tenders_pages:
        for tender in tenders:
            tender_id = tender.get('id')
            if not tender_id:
                continue

            details = get_tender_details(tender_id)
            if not details:
                continue

            status = details.get('status', '')
            if status != "active.tendering":
                continue

            items = details.get('items', []) or []
            raw_cpvs: List[str] = list({(item.get('classification', {}) or {}).get('id', '') for item in items if item.get('classification')})
            item_cpvs = [cpv.split('-')[0] if isinstance(cpv, str) else '' for cpv in raw_cpvs]
            matches_cpv = any((cpv or '').startswith(code) for cpv in item_cpvs for code in CPV_CODES)
            if not matches_cpv:
                continue
            cpv_display = ", ".join(sorted([cpv for cpv in item_cpvs if cpv])) or "Немає CPV коду"

            procuring_entity = details.get('procuringEntity', {}) or {}
            region = (procuring_entity.get('address', {}) or {}).get('region', '')
            if region not in ALLOWED_REGIONS:
                continue

            tender_period = details.get('tenderPeriod', {}) or {}
            deadline_str = tender_period.get('endDate', None)
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M")
                except Exception:
                    deadline = deadline_str
            else:
                deadline = "Немає дедлайну"

            # ЄДРПОУ замовника
            edrpou = (procuring_entity.get('identifier', {}) or {}).get('id', 'Немає ЄДРПОУ')
            # Посилання на тендер
            tender_url = f"https://prozorro.gov.ua/tender/{tender_id}"

            print(f"Tender ID: {tender_id}")
            print(f"Предмет закупівлі: {details.get('title', 'Немає назви')}")
            print(f"CPV Код: {cpv_display}")
            print(f"Статус: {details.get('status', 'Немає статусу')}")
            print(f"Дедлайн: {deadline}")
            print(f"Замовник: {procuring_entity.get('name', 'Немає замовника')}")
            print(f"ЄДРПОУ: {edrpou}")
            print(f"Сума: {details.get('value', {}).get('amount', 'немає бюджету')} {details.get('value', {}).get('currency', '')}")
            print(f"Посилання: {tender_url}")
            print("-" * 40)
            matches_found += 1
            time.sleep(0.2)

    if matches_found == 0:
        print("Нічого не знайдено за заданими фільтрами.")