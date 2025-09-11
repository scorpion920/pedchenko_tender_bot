"""
tender_api.py — модуль для роботи з ProZorro API.

Цей файл містить клас `ProZorroAPI`, який відповідає за:
- Виконання HTTP-запитів до API ProZorro
- Фільтрацію тендерів за CPV кодами та регіонами
- Підготовку текстових повідомлень для Telegram бота
- Підтримку пагінації та унікальності результатів
"""

import time
import logging
import requests
from typing import List, Dict

from config import (
    BASE_URL, CPV_CODES, ALLOWED_REGIONS, ALLOWED_REGION_KEYWORDS,
    SESSION_HEADERS, PAGE_LIMIT, MAX_PAGES, REQUEST_TIMEOUT, REQUEST_DELAY
)

logger = logging.getLogger(__name__)


class ProZorroAPI:
    """
    Клас для роботи з ProZorro API.

    Attributes:
        session (requests.Session): HTTP-сесія для повторного використання з'єднання
        seen_tenders (set): множина для збереження ID вже оброблених тендерів
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(SESSION_HEADERS)
        self.seen_tenders = set()

    def _is_region_allowed(self, address: str) -> bool:
        """
        Перевіряє, чи адреса замовника належить до дозволених регіонів.

        Args:
            address (str): рядок з адресою замовника

        Returns:
            bool: True, якщо адреса відповідає фільтру; False — інакше
        """
        if not address:
            return False
        return any(region in address for region in ALLOWED_REGIONS) or \
               any(keyword in address for keyword in ALLOWED_REGION_KEYWORDS)

    def _is_cpv_allowed(self, cpv_code: str) -> bool:
        """
        Перевіряє, чи CPV-код належить до дозволених.

        Args:
            cpv_code (str): CPV-код (класифікатор)

        Returns:
            bool: True, якщо код відповідає фільтру; False — інакше
        """
        return any(cpv_code.startswith(code[:4]) for code in CPV_CODES)

    def _fetch_page(self, offset: str = "") -> Dict:
        """
        Виконує HTTP-запит на отримання сторінки тендерів з API.

        Args:
            offset (str): курсор пагінації (по замовчуванню — порожній)

        Returns:
            dict: JSON-відповідь від API

        Raises:
            requests.RequestException: у випадку проблем з мережею
        """
        url = f"{BASE_URL}?limit={PAGE_LIMIT}&offset={offset}"
        logger.debug(f"Запит до API: {url}")

        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def search_tenders(self) -> List[str]:
        """
        Пошук актуальних тендерів за заданими фільтрами.

        Returns:
            List[str]: список текстових повідомлень про тендери
        """
        results = []
        offset = ""
        pages = 0

        try:
            while pages < MAX_PAGES:
                data = self._fetch_page(offset)
                tenders = data.get("data", [])
                offset = data.get("next_page", {}).get("offset")
                pages += 1

                logger.info(f"Отримано {len(tenders)} тендерів зі сторінки {pages}")

                for tender in tenders:
                    tender_id = tender.get("id")
                    if not tender_id or tender_id in self.seen_tenders:
                        continue

                    self.seen_tenders.add(tender_id)

                    procuring_entity = tender.get("procuringEntity", {})
                    address = procuring_entity.get("address", {}).get("region", "")
                    cpv_code = tender.get("classification", {}).get("id", "")

                    if not self._is_region_allowed(address):
                        continue
                    if not self._is_cpv_allowed(cpv_code):
                        continue

                    tender_info = (
                        f"📌 *{tender.get('title', 'Без назви')}*\n"
                        f"🏢 Замовник: {procuring_entity.get('name', 'Невідомо')}\n"
                        f"📍 Регіон: {address}\n"
                        f"🆔 ID: {tender.get('tenderID')}\n"
                        f"💰 Бюджет: {tender.get('value', {}).get('amount', 'Невідомо')} "
                        f"{tender.get('value', {}).get('currency', '')}\n"
                        f"🔗 [Деталі](https://prozorro.gov.ua/tender/{tender_id})"
                    )
                    results.append(tender_info)

                if not offset:  # Якщо більше немає сторінок
                    break

                time.sleep(REQUEST_DELAY)

        except requests.RequestException as e:
            logger.error(f"Помилка мережі при запиті до ProZorro API: {e}")
        except Exception as e:
            logger.exception(f"Несподівана помилка при пошуку тендерів: {e}")

        return results
