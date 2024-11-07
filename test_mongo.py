from pymongo import MongoClient

# Підключення до MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Спроба отримати список баз даних
try:
    databases = client.list_database_names()
    print("Успішно підключено! Список баз даних:")
    print(databases)
except Exception as e:
    print("Помилка підключення:", e)
