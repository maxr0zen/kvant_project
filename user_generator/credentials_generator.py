import hashlib

def generate_credentials(last_name, first_name):
    """
    Генерация логина и пароля на основе фамилии и имени пользователя.
    Логин и пароль будут одинаковыми для одинаковых входных данных.
    
    :param last_name: Фамилия пользователя
    :param first_name: Имя пользователя
    :return: Логин и пароль
    """
    # Создаем строку на основе фамилии и имени
    data = f"{last_name.lower()}{first_name.lower()}"
    
    # Генерация логина: первые 3 буквы фамилии + первые 3 буквы имени + хэш (первые 4 цифры)
    login_base = (last_name[:3] + first_name[:3]).lower()
    hash_part = hashlib.md5(data.encode()).hexdigest()[:4]  # Берем первые 4 символа хэша
    login = f"{login_base}{hash_part}"
    
    # Генерация пароля: хэш на основе данных (первые 8 символов)
    password = hashlib.sha256(data.encode()).hexdigest()[:8]
    
    return login, password