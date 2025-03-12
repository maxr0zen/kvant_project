from pymongo import MongoClient
from credentials_generator import generate_credentials
import uuid  # Импортируем библиотеку для генерации уникальных ID

def create_user(last_name, first_name, group):
    """
    Создание пользователя в MongoDB.
    
    :param last_name: Фамилия пользователя
    :param first_name: Имя пользователя
    :param group: Группа пользователя
    :return: Логин, пароль и ID пользователя
    """
    # Генерация логина и пароля
    login, password = generate_credentials(last_name, first_name)
    
    # Генерация уникального ID пользователя
    user_id = str(uuid.uuid4())  # Генерируем уникальный ID
    
    # Подключение к MongoDB
    print("Подключаемся к MongoDB...")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['kvant_users']  
    collection = db['users']  
    print("Успешное подключение к базе данных.")
    
    # Создание документа пользователя
    user = {
        "_id": user_id,  # Добавляем уникальный ID
        "last_name": last_name,
        "first_name": first_name,
        "group": group,
        "login": login,
        "password": password
    }
    
    # Вставка документа в коллекцию
    print(f"Добавляем пользователя {last_name} {first_name} в коллекцию 'users'...")
    collection.insert_one(user)
    print("Пользователь успешно добавлен.")
    
    # Закрытие соединения с MongoDB
    client.close()
    print("Соединение с базой данных закрыто.")
    
    return login, password, user_id  # Возвращаем логин, пароль и ID

# Пример использования
if __name__ == "__main__":
    last_name = "Учитель" 
    first_name = "Учительский"
    group = "superuser"

    # Получаем логин, пароль и ID
    login, password, user_id = create_user(last_name, first_name, group)
    print(f"Логин: {login}, Пароль: {password}, ID: {user_id}")

    # Пример получения логина и пароля по данным пользователя
    test_login, test_password = generate_credentials(last_name, first_name)
    print(f"Тестовый логин: {test_login}, Тестовый пароль: {test_password}")