import requests

print("🚀 Скрипт стартував!")


BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"

CPV_CODES = [
    "15420000", "15330000", "15320000", "15610000", "15620000", "15810000", 
    "15820000", "15830000", "15840000", "15850000", "15860000", "15870000", 
    "15980000"
]

def get_tenders(limit=20):
    try:
        response = requests.get(BASE_URL, params={'limit': limit})
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.RequestException as e:
        print(f"Помилка отримання тендерів: {e}")
        return []
    

def get_tender_details(tender_id):
    try:
        url = f"{BASE_URL}/{tender_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.RequestException as e:
        print(f"Помилка отримання деталей тендера {tender_id}: {e}")
        return {}
    
tenders = get_tenders(limit=50)

if not tenders:
    print("Тендери не знайдені.")
else:
    for tender in tenders:
        tender_id = tender.get('id')
        details = get_tender_details(tender_id)

        status = details.get('status', '')
        if status != 'active':
            continue

        cpv = details.get('items', [{}])[0].get('classification', {}).get('id', '')
        if not any(cpv.startswith(code) for code in CPV_CODES):
            continue

        cpv_display = cpv if cpv else "Немає CPV коду"
                
        print(f"Tender ID: {tender_id}")
        print(f"Предмет закупівлі: {details.get('title', 'Немає назви')}")
        print(f"CPV Код: {cpv_display}")
        print(f"Статус: {details.get('status', 'Немає статусу')}")
        print(f"Замовник: {details.get('procuringEntity', {}).get('name', 'Немає замовника')}")
        print(f"Сума: {details.get('value', {}).get('amount', 'немає бюджету')} {details.get('value', {}).get('currency', '')}")
        print("-" * 40)

