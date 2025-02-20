# app/db/mongodb.py
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

# Подключение к MongoDB
try:
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]
    collection = db['users']  # Коллекция пользователей
    user_progress_collection = db["user_progress"]

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

def update_user_progress(login: str, block_id: int, task_id: int, status: str):
    """
    Обновляет или создает запись о прогрессе пользователя.
    """
    user_progress_collection.update_one(
        {"login": login, "block_id": block_id, "task_id": task_id},
        {
            "$set": {
                "status": status
            }
        },
        upsert=True  # Создать запись, если она не существует
    )

def get_user_progress(login: str, block_id: int = None, task_id: int = None):
    """
    Получает прогресс пользователя.
    Если block_id и task_id не указаны, возвращает весь прогресс пользователя.
    """
    query = {"login": login}
    if block_id:
        query["block_id"] = block_id
    if task_id:
        query["task_id"] = task_id
    
    return list(user_progress_collection.find(query))