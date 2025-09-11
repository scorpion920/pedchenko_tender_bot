"""
Модуль для роботи з ProZorro API
"""
import requests
import time
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

from config import (
    BASE_URL, CPV_CODES, ALLOWED_REGIONS, ALLOWED_REGION_KEYWORDS,
    SESSION_HEADERS, PAGE_LIMIT, MAX_PAGES, REQUEST_TIMEOUT, REQUEST_DELAY
)


class ProZorroAPI:
    """Клас для роботи з ProZorro API"""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Створення HTTP сесії з retry логікою"""
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
    
    def get_tenders(self, limit: int = PAGE_LIMIT) -> Dict:
        """Отримання списку тендерів"""
        try:
            response = self.session.get(
                BASE_URL,
                params={"limit": limit, "descending": 1},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Помилка отримання тендерів: {e}")
            return {}
    
    def get_tender_details(self, tender_id: str) -> Dict:
        """Отримання деталей конкретного тендера"""
        try:
            url = f"{BASE_URL}/{tender_id}"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get('data', {})
        except requests.RequestException as e:
            print(f"Помилка деталей тендера {tender_id}: {e}")
            return {}
    
    def fetch_tenders_with_pagination(self) -> List[Dict]:
        """Отримання тендерів з пагінацією"""
        first_page = self.get_tenders(limit=PAGE_LIMIT)
        if not first_page or not first_page.get('data'):
            return []

        next_offset = (first_page.get('next_page') or {}).get('offset')
        tenders_pages = [first_page.get('data', [])]

        for _ in range(MAX_PAGES - 1):
            if not next_offset:
                break
            try:
                page = self.session.get(
                    BASE_URL,
                    params={"limit": PAGE_LIMIT, "descending": 1, "offset": next_offset},
                    timeout=REQUEST_TIMEOUT,
                )
                page.raise_for_status()
                page_json = page.json()
                tenders_pages.append(page_json.get('data', []))
                next_offset = (page_json.get('next_page') or {}).get('offset')
            except Exception:
                break

        return tenders_pages
    
    def filter_tenders(self, tenders_pages: List[List[Dict]]) -> List[Dict]:
        """Фільтрація тендерів за заданими критеріями"""
        results = []
        
        for tenders in tenders_pages:
            for tender in tenders:
                tender_id = tender.get('id')
                if not tender_id:
                    continue

                details = self.get_tender_details(tender_id)
                if not details:
                    continue

                # Фільтр по статусу
                if details.get('status') != "active.tendering":
                    continue

                # Фільтр по CPV кодах
                if not self._matches_cpv(details):
                    continue

                # Фільтр по регіону
                if not self._matches_region(details):
                    continue

                results.append(details)
                time.sleep(REQUEST_DELAY)

        return results
    
    def _matches_cpv(self, details: Dict) -> bool:
        """Перевірка відповідності CPV кодів"""
        items = details.get('items', []) or []
        raw_cpvs = list({
            (item.get('classification', {}) or {}).get('id', '') 
            for item in items if item.get('classification')
        })
        item_cpvs = [cpv.split('-')[0] if isinstance(cpv, str) else '' for cpv in raw_cpvs]
        return any((cpv or '').startswith(code) for cpv in item_cpvs for code in CPV_CODES)
    
    def _matches_region(self, details: Dict) -> bool:
        """Перевірка відповідності регіону"""
        procuring_entity = details.get('procuringEntity', {}) or {}
        region = (procuring_entity.get('address', {}) or {}).get('region', '')
        return (
            region in ALLOWED_REGIONS or 
            any(kw in region for kw in ALLOWED_REGION_KEYWORDS)
        )
    
    def format_tender_message(self, details: Dict) -> str:
        """Форматування повідомлення про тендер"""
        items = details.get('items', []) or []
        raw_cpvs = list({
            (item.get('classification', {}) or {}).get('id', '') 
            for item in items if item.get('classification')
        })
        item_cpvs = [cpv.split('-')[0] if isinstance(cpv, str) else '' for cpv in raw_cpvs]

        tender_period = details.get('tenderPeriod', {}) or {}
        deadline_str = tender_period.get('endDate', None)
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(
                    deadline_str.replace("Z", "+00:00")
                ).strftime("%d.%m.%Y %H:%M")
            except Exception:
                deadline = deadline_str
        else:
            deadline = "Немає дедлайну"

        procuring_entity = details.get('procuringEntity', {}) or {}
        edrpou = (procuring_entity.get('identifier', {}) or {}).get('id', 'Немає ЄДРПОУ')
        tender_url = f"https://prozorro.gov.ua/tender/{details.get('id')}"

        message = (
            f"📌 Новий тендер!\n"
            f"🆔 ID тендера: {details.get('id')}\n"
            f"📋 Предмет закупівлі: {details.get('title', 'Немає назви')}\n"
            f"🏷️ CPV Код: {', '.join(item_cpvs)}\n"
            f"📊 Статус: {details.get('status', 'Немає статусу')}\n"
            f"⏰ Дедлайн: {deadline}\n"
            f"🏢 Замовник: {procuring_entity.get('name', 'Немає замовника')}\n"
            f"🆔 ЄДРПОУ: {edrpou}\n"
            f"💰 Сума: {details.get('value', {}).get('amount', 'немає бюджету')} "
            f"{details.get('value', {}).get('currency', '')}\n"
            f"🔗 Посилання: {tender_url}"
        )
        return message
    
    def search_tenders(self) -> List[str]:
        """Основна функція пошуку тендерів"""
        tenders_pages = self.fetch_tenders_with_pagination()
        filtered_tenders = self.filter_tenders(tenders_pages)
        
        messages = []
        for tender in filtered_tenders:
            messages.append(self.format_tender_message(tender))
        
        return messages
