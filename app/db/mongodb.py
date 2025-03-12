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
    blocks_collection = db["blocks"]
    user_progress_collection = db["user_progress"]
    lectures_collection = db["lectures"]
    

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

def generate_task_id():
    # Генерация уникального ID для задания
    last_task = blocks_collection.find_one(
        {},
        {"tasks": {"$slice": -1}},  # Получаем последнее задание
        sort=[("tasks.task_id", -1)]  # Сортируем по task_id в порядке убывания
    )
    if last_task and "tasks" in last_task and last_task["tasks"]:
        return last_task["tasks"][-1]["task_id"] + 1
    return 1  # Если заданий нет, начинаем с 1

def generate_block_id():
    # Генерация уникального ID для блока
    last_block = blocks_collection.find_one(
        {},
        sort=[("block_id", -1)]  # Сортируем по block_id в порядке убывания
    )
    if last_block:
        return last_block["block_id"] + 1
    return 1  # Если блоков нет, начинаем с 1

def generate_lecture_id():
    last_lecture = lectures_collection.find_one({}, sort=[("lecture_id", -1)])
    if last_lecture:
        return last_lecture["lecture_id"] + 1
    return 1

async def add_lecture(title: str, content: str, code_snippets: list = None):
    if code_snippets is None:
        code_snippets = []
    
    lecture = {
        "lecture_id": generate_lecture_id(),
        "title": title,
        "content": content,
        "code_snippets": code_snippets
    }
    lectures_collection.insert_one(lecture)
    return lecture
    
def get_lecture_by_id(lecture_id: int):
    return lectures_collection.find_one({"lecture_id": lecture_id})

def update_lecture(lecture_id: int, title: str = None, content: str = None, code_snippets: list = None):
    update_data = {"updated_at": datetime.utcnow()}
    
    if title:
        update_data["title"] = title
    if content:
        update_data["content"] = content
    if code_snippets:
        update_data["code_snippets"] = code_snippets
    
    lectures_collection.update_one(
        {"lecture_id": lecture_id},
        {"$set": update_data}
    )
    return lectures_collection.find_one({"lecture_id": lecture_id})

def delete_lecture(lecture_id: int):
    result = lectures_collection.delete_one({"lecture_id": lecture_id})
    return result.deleted_count > 0  # Возвращает True, если лекция была удалена

def get_all_lectures():
    return list(lectures_collection.find({}))