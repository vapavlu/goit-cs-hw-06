# Використовуємо офіційний Python образ
FROM python:3.9-slim

# Встановлюємо необхідні бібліотеки
RUN pip install pymongo

# Створюємо директорію для додатку
WORKDIR /app

# Копіюємо всі файли в контейнер
COPY . /app

# Відкриваємо порти для HTTP (3000) і сокет-сервера (5000)
EXPOSE 3000 5000

# Запускаємо main.py
CMD ["python", "main.py"]
