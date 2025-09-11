# Використовуємо офіційний Python
FROM python:3.12-slim

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файли проекту
COPY . /app

# Встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Змінні оточення (для прикладу, але на сервері краще через .env)
# ENV TELEGRAM_TOKEN=your_token_here
# ENV CHAT_ID=your_chat_id_here

# Команда для запуску бота
CMD ["python", "bot.py"]
