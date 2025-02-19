import io
import sys
from pymongo import MongoClient

class CodeTester:
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        # Ограничиваем встроенные функции и модули
        self.allowed_builtins = {
            "print": print,
            "int": int,
            "str": str,
            "float": float,
            "len": len,
            "range": range,
            "sum": sum,
            "max": max,
            "min": min,
        }
        self.safe_globals = {"__builtins__": self.allowed_builtins}
        self.safe_locals = {}

        # Подключение к MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client["test_cases_db"]
        self.blocks_collection = self.db["blocks"]

    def run_code(self, code, input_data):
        """Безопасное выполнение кода с входными данными и перехватом вывода."""
        try:
            # Переопределяем input для использования входных данных
            def safe_input(prompt=""):
                if not hasattr(self, "input_data"):
                    raise ValueError("Входные данные не предоставлены.")
                if not self.input_data:
                    raise ValueError("Входные данные закончились.")
                return self.input_data.pop(0)

            self.safe_globals["input"] = safe_input
            self.input_data = input_data.split("\n") if input_data else []

            # Перехватываем вывод print
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            # Выполняем код
            exec(code, self.safe_globals, self.safe_locals)

            # Восстанавливаем стандартный вывод
            sys.stdout = old_stdout

            # Возвращаем результат (последний вывод print)
            output = buffer.getvalue().strip()
            return output
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def get_test_cases_from_db(self, task_id):
        """Извлекает тесткейсы из MongoDB по task_id."""
        task = self.blocks_collection.find_one({"tasks.task_id": task_id}, {"tasks.$": 1})
        if not task:
            raise ValueError(f"Задача с ID {task_id} не найдена.")
        return task["tasks"][0]["test_cases"]

    def test_code(self, code, test_cases):
        """Тестирование кода на нескольких тесткейсах."""
        results = []
        for i, test_case in enumerate(test_cases):
            input_data = test_case["input"]
            expected_output = test_case["expected_output"]

            # Выполняем код с входными данными
            actual_output = self.run_code(code, input_data)

            # Сравниваем результат с ожидаемым
            if actual_output == expected_output:
                results.append(f"Тест {i + 1} пройден: {actual_output} == {expected_output}")
            else:
                results.append(f"Тест {i + 1} не пройден: {actual_output} != {expected_output}")
        return results

    def test_code_with_db(self, code, task_id):
        """Тестирование кода с использованием тесткейсов из MongoDB."""
        # Получаем тесткейсы из базы данных
        test_cases = self.get_test_cases_from_db(task_id)

        # Запускаем тестирование
        return self.test_code(code, test_cases)