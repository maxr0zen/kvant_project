from pymongo import MongoClient

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["kvant_users"]  # Создаем базу данных
collection = db["blocks"]  # Создаем коллекцию "blocks"

# Пример данных для заполнения
blocks = [
    {
        "block_id": 1,
        "block_name": "Блок 1: Арифметика",
        "tasks": [
            {
                "task_id": 1,
                "task_name": "Сложение двух чисел",
                "task_description": "Вам нужно считать данные, которые подаются на вход используя input() и вывести их сумму используя print()",
                "test_cases": [
                    {"input": "2\n3\n", "expected_output": "5"},
                    {"input": "10\n20\n", "expected_output": "30"},
                    {"input": "-1\n1\n", "expected_output": "0"},
                ],
            },
            {
                "task_id": 2,
                "task_name": "Умножение двух чисел",
                "task_description": "Вам нужно считать данные, которые подаются на вход используя input() и вывести их произведение используя print()",
                "test_cases": [
                    {"input": "2\n3\n", "expected_output": "6"},
                    {"input": "10\n20\n", "expected_output": "200"},
                    {"input": "-1\n1\n", "expected_output": "-1"},
                ],
            },
        ],
    },
    {
        "block_id": 2,
        "block_name": "Блок 2: Работа со строками",
        "tasks": [
            {
                "task_id": 3,
                "task_name": "Конкатенация строк",
                "task_description": "Вам нужно считать строки, которые подаются на вход используя input() и вывести их используя print()",
                "test_cases": [
                    {"input": "Hello\nWorld\n", "expected_output": "HelloWorld"},
                    {"input": "foo\nbar\n", "expected_output": "foobar"},
                ],
            },
            {
                "task_id": 4,
                "task_name": "Длина строки",
                "task_description": "Вам нужно считать строку, которая подаётся на вход и вывести её длинну",
                "test_cases": [
                    {"input": "Hello\n", "expected_output": "5"},
                    {"input": "Python\n", "expected_output": "6"},
                ],
            },
        ],
    },
]

# Очистка коллекции перед заполнением (опционально)
collection.delete_many({})

# Заполнение коллекции данными
collection.insert_many(blocks)

print("База данных успешно заполнена!")