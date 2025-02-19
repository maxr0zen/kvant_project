# app/db/mongodb.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

# Подключение к MongoDB
try:
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    collection = db['users']  # Коллекция пользователей
    print("Connected to MongoDB successfully!")
except ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    raise

# Функция для получения пользователя по логину
def get_user_by_login(login: str):
    """
    Находит пользователя по логину.
    :param login: Логин пользователя.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
    return collection.find_one({"login": login})

# Функция для создания нового пользователя
def create_user(user_data: dict):
    """
    Создает нового пользователя.
    :param user_data: Словарь с данными пользователя.
    :return: ID созданного пользователя.
    """
    result = collection.insert_one(user_data)
    return result.inserted_id

# Функция для обновления данных пользователя
def update_user(user_id: str, update_data: dict):
    """
    Обновляет данные пользователя.
    :param user_id: ID пользователя.
    :param update_data: Словарь с обновляемыми данными.
    :return: Количество измененных документов.
    """
    result = collection.update_one({"_id": user_id}, {"$set": update_data})
    return result.modified_count

# Функция для удаления пользователя
def delete_user(user_id: str):
    """
    Удаляет пользователя по ID.
    :param user_id: ID пользователя.
    :return: Количество удаленных документов.
    """
    result = collection.delete_one({"_id": user_id})
    return result.deleted_count