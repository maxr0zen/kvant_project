from code_tester import CodeTester

# Пример кода для тестирования
code = """
print(int(input()) + int(input()))
"""

# ID задачи, которую нужно протестировать
task_id = 1

# Создаем экземпляр тестера
tester = CodeTester()

# Запускаем тестирование с использованием тесткейсов из MongoDB
results = tester.test_code_with_db(code, task_id)

# Выводим результаты
for result in results:
    print(result)