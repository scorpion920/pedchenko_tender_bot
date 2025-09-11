# Бот моніторингу тендерів ProZorro

Telegram бот для автоматичного моніторингу тендерів на платформі ProZorro.

## Можливості

- 🔍 Пошук тендерів за заданими критеріями
- 🤖 Автоматичні сповіщення кожні 10 хвилин
- 📱 Зручний інтерфейс через Telegram
- 🎯 Фільтрація за регіонами та CPV кодами
- ⚡ Швидка робота з оптимізованими запитами

## Фільтри пошуку

- **Статус**: `active.tendering` (прийом пропозицій)
- **Регіони**: Київ, Черкаси
- **CPV коди**: Будівництво та ремонт (1542xxx-1598xxx)

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone <repository-url>
cd tender-bot
```

2. Створіть віртуальне середовище:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Встановіть залежності:
```bash
pip install -r requirements.txt
```

4. Налаштуйте змінні середовища (опціонально):
```bash
# Створіть файл .env
TELEGRAM_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
```

## Конфігурація

Основні налаштування знаходяться у файлі `config.py`:

- `TELEGRAM_TOKEN` - токен Telegram бота
- `CHAT_ID` - ID чату для сповіщень
- `CPV_CODES` - список CPV кодів для пошуку
- `ALLOWED_REGIONS` - дозволені регіони
- `CHECK_INTERVAL` - інтервал перевірки (секунди)

## Запуск

```bash
python bot.py
```

## Команди бота

- `/start` - Головне меню
- `/help` - Довідка
- `/tenders` - Ручний пошук тендерів

## Структура проекту

```
tender-bot/
├── bot.py              # Основний файл бота
├── tender_api.py       # Модуль для роботи з ProZorro API
├── config.py           # Конфігурація
├── requirements.txt    # Залежності
└── README.md          # Документація
```

## Отримання токена бота

1. Напишіть @BotFather в Telegram
2. Відправте команду `/newbot`
3. Слідуйте інструкціям для створення бота
4. Скопіюйте отриманий токен в `config.py`

## Отримання Chat ID

1. Напишіть вашому боту будь-яке повідомлення
2. Перейдіть по посиланню: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Знайдіть `"chat":{"id":` в відповіді - це ваш Chat ID

## Ліцензія

MIT License
