# app/api/v1/endpoints/code_tester_router.py
from fastapi import APIRouter, HTTPException
from code_test.code_tester import CodeTester

router = APIRouter()

# Инициализация CodeTester
code_tester = CodeTester()

@router.post("/test-code")
async def test_code(code: str, test_cases: list):
    """
    Тестирование кода с предоставленными тест-кейсами.
    :param code: Код для тестирования.
    :param test_cases: Список тест-кейсов.
    :return: Результаты тестирования.
    """
    try:
        results = code_tester.test_code(code, test_cases)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-code-from-db")
async def test_code_from_db(code: str, task_id: str):
    """
    Тестирование кода с использованием тест-кейсов из MongoDB.
    :param code: Код для тестирования.
    :param task_id: ID задачи для получения тест-кейсов.
    :return: Результаты тестирования.
    """
    try:
        results = code_tester.test_code_with_db(code, task_id)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))