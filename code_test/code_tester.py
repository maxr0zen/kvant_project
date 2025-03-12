import io
import os
import sys
import ast
import time
import signal
import platform
import asyncio
import inspect
import multiprocessing
import ctypes
from typing import Dict, Any, Optional, List
from concurrent.futures import ProcessPoolExecutor
from pymongo import MongoClient
from functools import partial
import weakref
import logging

logger = logging.getLogger(__name__)

class CodeExecutor:
    """Безопасное выполнение кода в отдельном процессе"""
    
    ALLOWED_BUILTINS = {
        'print': print,
        'len': len,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'min': min,
        'max': max,
        'sum': sum,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'reversed': reversed,
        'all': all,
        'any': any,
        'chr': chr,
        'ord': ord,
        'pow': pow,
        'isinstance': isinstance,
    }

    ALLOWED_AST_NODES = {
        ast.Module, ast.Expr, ast.Load, ast.Store, ast.Call, ast.Name, ast.Constant,
        ast.List, ast.Tuple, ast.Set, ast.Dict, ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.BoolOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
        ast.Pow, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq, ast.And, ast.Or,
        ast.Not, ast.If, ast.For, ast.While, ast.Break, ast.Continue, ast.Return,
        ast.FunctionDef, ast.Lambda, ast.arguments, ast.arg, ast.Assert, ast.Assign,
        ast.AugAssign, ast.Pass, ast.Slice, ast.Subscript, ast.ListComp, ast.comprehension
    }

    @classmethod
    def execute(cls, code: str, input_data: str = "") -> Dict[str, Any]:
        """Выполняет код в изолированной среде"""
        # Перенаправляем stdout
        stdout = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = stdout

        try:
            # Проверяем код на безопасность
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if type(node) not in cls.ALLOWED_AST_NODES:
                    raise SecurityError(f"Запрещенная операция: {type(node).__name__}")

            # Создаем безопасное окружение
            globals_dict = {'__builtins__': cls.ALLOWED_BUILTINS}
            locals_dict = {}

            # Подготавливаем input
            if input_data:
                input_lines = iter(input_data.split('\n'))
                globals_dict['input'] = lambda _=None: next(input_lines, '')

            # Выполняем код
            exec(compile(tree, '<string>', 'exec'), globals_dict, locals_dict)

            # Получаем результат
            output = stdout.getvalue()
            result = locals_dict.get('result')

            return {
                "output": output if output else None,
                "result": result,
                "error": None
            }

        except Exception as e:
            return {"error": str(e), "output": None, "result": None}

        finally:
            sys.stdout = original_stdout
            stdout.close()

class CodeTester:
    """Тестирование кода с использованием процессов"""

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/", timeout: int = 5):
        self.timeout = timeout
        self.client = MongoClient(mongo_uri)
        self.db = self.client["test_cases_db"]
        self.executor = ProcessPoolExecutor(max_workers=1)

    async def run_code(self, code: str, input_data: str = "") -> Dict[str, Any]:
        """Запускает код на выполнение в отдельном процессе"""
        try:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self.executor,
                CodeExecutor.execute,
                code,
                input_data
            )
            
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result

        except asyncio.TimeoutError:
            return {
                "error": f"Превышено время выполнения ({self.timeout} сек)",
                "output": None,
                "result": None
            }
        except Exception as e:
            logger.error(f"Error running code: {str(e)}", exc_info=True)
            return {"error": str(e), "output": None, "result": None}

    async def test_code(self, code: str, test_cases: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Тестирует код на наборе тест-кейсов"""
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            result = await self.run_code(code, test_case["input"])
            
            if result.get("error"):
                results.append({
                    "passed": False,
                    "error": result["error"],
                    "message": f"Тест {i}: {result['error']}",
                    "actual_output": None
                })
                continue

            actual = result["output"] or str(result["result"])
            if actual is None:
                actual = ""
                
            expected = test_case["expected_output"].strip()
            actual = actual.rstrip('\n')
            
            passed = actual == expected
            
            results.append({
                "passed": passed,
                "message": f"Тест {i} {'пройден' if passed else 'не пройден'}: '{actual}' {'==' if passed else '!='} '{expected}'",
                "actual_output": actual
            })
            
        return results

    def get_test_cases(self, task_id: int) -> List[Dict[str, str]]:
        """Получает тест-кейсы из базы данных"""
        task = self.db["blocks"].find_one(
            {"tasks.task_id": task_id},
            {"tasks.$": 1}
        )
        if not task:
            raise ValueError(f"Задача с ID {task_id} не найдена")
        return task["tasks"][0]["test_cases"]

    async def cleanup(self):
        """Очищает ресурсы"""
        self.executor.shutdown(wait=False)
        if hasattr(self, 'client'):
            self.client.close()

class CodeTesterManager:
    """Управление экземплярами CodeTester"""
    
    def __init__(self):
        self._testers: Dict[str, CodeTester] = {}
        self._lock = asyncio.Lock()
    
    async def get_tester(self, user_id: str) -> CodeTester:
        """Получает или создает экземпляр CodeTester"""
        async with self._lock:
            if user_id not in self._testers:
                self._testers[user_id] = CodeTester()
            return self._testers[user_id]
    
    async def cleanup_user(self, user_id: str):
        """Очищает ресурсы пользователя"""
        async with self._lock:
            if user_id in self._testers:
                await self._testers[user_id].cleanup()
                del self._testers[user_id]
    
    async def shutdown(self):
        """Завершает работу всех тестеров"""
        async with self._lock:
            for tester in self._testers.values():
                await tester.cleanup()
            self._testers.clear()

class SecurityError(Exception):
    """Исключение безопасности"""
    pass

def terminate_process(pid):
    """Безопасное завершение процесса в Windows"""
    try:
        if platform.system() == 'Windows':
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, 0, pid)
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass

def execute_code_in_process(code, input_data, allowed_builtins):
    """Выполняет код в отдельном процессе"""
    try:
        # Сохраняем PID текущего процесса
        current_pid = multiprocessing.current_process().pid
        
        # Перенаправляем стандартный вывод
        buffer = io.StringIO()
        sys.stdout = buffer

        # Создаем безопасное окружение для выполнения кода
        safe_globals = {"__builtins__": allowed_builtins}
        safe_locals = {}

        # Подготавливаем input данные
        if input_data:
            input_lines = input_data.split("\n")
            input_iter = iter(input_lines)
            def safe_input(prompt=""):
                try:
                    return next(input_iter)
                except StopIteration:
                    raise ValueError("Входные данные закончились.")
            safe_globals["input"] = safe_input

        # Выполняем код
        exec(code, safe_globals, safe_locals)
        
        # Получаем вывод
        output = buffer.getvalue().strip()
        
        # Проверяем результат выполнения
        if not output:
            # Если нет вывода, проверяем, есть ли возвращаемое значение
            if 'result' in safe_locals:
                return {"output": str(safe_locals['result']), "has_output": False, "has_result": True}
            return {"output": "", "has_output": False, "has_result": False}
        return {"output": output, "has_output": True, "has_result": False}
    except Exception as e:
        return {"error": str(e)}
    finally:
        sys.stdout = sys.__stdout__

class ProcessPoolWrapper:
    """Обертка для ProcessPoolExecutor с автоматическим восстановлением"""
    def __init__(self, max_workers=1):
        self.max_workers = max_workers
        self.pool = None
        self.create_pool()
    
    def create_pool(self):
        """Создает новый пул процессов"""
        if self.pool is not None:
            try:
                self.pool.shutdown(wait=False)
            except Exception:
                pass
        try:
            self.pool = ProcessPoolExecutor(max_workers=self.max_workers)
        except Exception:
            # Если не удалось создать пул, создаем новый с задержкой
            time.sleep(0.1)
            self.pool = ProcessPoolExecutor(max_workers=self.max_workers)
    
    async def execute(self, func, *args, **kwargs):
        """Выполняет функцию в пуле с автоматическим восстановлением при сбое"""
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            if self.pool is None:
                self.create_pool()
                
            try:
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(self.pool, func, *args, **kwargs)
                try:
                    result = await asyncio.wait_for(future, timeout=30)  # Добавляем таймаут
                    return result
                except asyncio.TimeoutError:
                    # Если превышено время выполнения, пересоздаем пул
                    self.create_pool()
                    raise
            except (ProcessLookupError, OSError, RuntimeError) as e:
                last_error = e
                retry_count += 1
                # Пересоздаем пул при ошибке
                self.create_pool()
                if retry_count == max_retries:
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                last_error = e
                if retry_count == max_retries - 1:
                    break
                retry_count += 1
                self.create_pool()
                await asyncio.sleep(0.1)
        
        # Если все попытки исчерпаны, возвращаем ошибку
        error_msg = str(last_error) if last_error else "Неизвестная ошибка"
        return {"error": f"Ошибка выполнения кода после {max_retries} попыток: {error_msg}"}

    async def test_code_with_db(self, code, task_id):
        """Асинхронное тестирование кода с использованием тесткейсов из MongoDB."""
        # Получаем тесткейсы из базы данных
        test_cases = self.get_test_cases_from_db(task_id)

        # Запускаем тестирование
        return await self.test_code(code, test_cases)

    def get_test_cases_from_db(self, task_id):
        """Извлекает тесткейсы из MongoDB по task_id."""
        task = self.blocks_collection.find_one({"tasks.task_id": task_id}, {"tasks.$": 1})
        if not task:
            raise ValueError(f"Задача с ID {task_id} не найдена.")
        return task["tasks"][0]["test_cases"]

    def __del__(self):
        """Очистка ресурсов при удалении объекта"""
        if hasattr(self, 'pool'):
            self.pool.shutdown(wait=False)