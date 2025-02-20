from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db.mongodb import get_user_by_login, get_user_progress
from pymongo import MongoClient
from code_test.code_tester import CodeTester
import logging
from datetime import datetime
from app.db.mongodb import update_user_progress
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Настройка Jinja2
templates = Jinja2Templates(directory="templates")

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["kvant_users"]
blocks_collection = db["blocks"]
users_collection = db["users"]

# Инициализация CodeTester
code_tester = CodeTester()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    SessionMiddleware,
    secret_key="kvant_top",  # Секретный ключ для подписи сессий
    session_cookie="session_cookie"   # Имя cookie для сессии
)

# Маршрут для отображения страницы авторизации
@app.get("/", response_class=HTMLResponse)
async def read_login_page(request: Request):
    logger.info("Отображение страницы авторизации")
    return templates.TemplateResponse("login.html", {"request": request})

# Маршрут для обработки данных из формы
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, login: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"login": login, "password": password})
    
    if user and user['password'] == password:
        # Сохраняем login в сессии
        request.session["login"] = login
        logger.info(f"Пользователь {login} успешно авторизован")
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        logger.warning(f"Неверный логин или пароль для пользователя {login}")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

# Роут для dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard_page(request: Request):
    # Получаем login из сессии
    login = request.session.get("login")
    if not login:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    logger.info(f"Пользователь {login} открыл dashboard")
    
    # Получаем все блоки заданий из MongoDB
    blocks = list(blocks_collection.find({}))
    
    # Получаем прогресс пользователя
    user_progress = get_user_progress(login)
    
    # Создаем словарь для хранения статусов заданий
    task_status = {}
    for progress in user_progress:
        key = (progress["block_id"], progress["task_id"])
        task_status[key] = progress["status"]
    
    # Разделяем задания на три группы
    not_started = []
    in_progress = []
    completed = []
    
    for block in blocks:
        for task in block["tasks"]:
            key = (block["block_id"], task["task_id"])
            status = task_status.get(key, "not_started")  # По умолчанию "not_started"
            
            task_info = {
                "block_id": block["block_id"],
                "block_name": block["block_name"],
                "task_id": task["task_id"],
                "task_name": task["task_name"],
                "task_description": task["task_description"],
                "status": status
            }
            
            if status == "not_started":
                not_started.append(task_info)
            elif status == "in_progress":
                in_progress.append(task_info)
            elif status == "completed":
                completed.append(task_info)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "blocks": blocks,
            "not_started": not_started,
            "in_progress": in_progress,
            "completed": completed
        }
    )

# Маршрут для отображения страницы задания
@app.get("/task/{block_id}/{task_id}", response_class=HTMLResponse)
async def show_task(request: Request, block_id: int, task_id: int):
    logger.info(f"Отображение страницы задания: block_id={block_id}, task_id={task_id}")
    
    # Получаем задание из MongoDB
    task = blocks_collection.find_one(
        {"block_id": block_id, "tasks.task_id": task_id},
        {"tasks.$": 1, "block_name": 1}
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    current_task = task["tasks"][0]
    return templates.TemplateResponse(
        "task.html",
        {
            "request": request,
            "block_name": task["block_name"],
            "task_name": current_task["task_name"],
            "task_description": current_task["task_description"],
            "task_id": current_task["task_id"],
            "test_cases": current_task["test_cases"]
        }
    )

# Маршрут для обработки отправки кода
@app.post("/task/{block_id}/{task_id}", response_class=HTMLResponse)
async def submit_code(
    request: Request,
    block_id: int,
    task_id: int,
    code: str = Form(...),
    login: str = Form(...) 
):
    login = request.session.get("login")
    logger.info(f"Получен login: {login}")
    logger.info(f"Обработка отправки кода: block_id={block_id}, task_id={task_id}")
    
    # Получаем задание из MongoDB, включая block_name
    task = blocks_collection.find_one(
        {"block_id": block_id, "tasks.task_id": task_id},
        {"tasks.$": 1, "block_name": 1}  # Включаем block_name в результат
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    # Извлекаем тест-кейсы
    test_cases = task["tasks"][0]["test_cases"]
    
    # Тестируем код
    results = []
    all_tests_passed = True  # По умолчанию считаем, что все тесты пройдены

    try:
        # Проверяем, есть ли синтаксические ошибки в коде
        compile(code, "<string>", "exec")
        
        # Если синтаксических ошибок нет, тестируем код
        results = code_tester.test_code(code, test_cases)
        
        # Проверяем, есть ли в результатах слово "не"
        for result in results:
            if "не" in result:
                all_tests_passed = False
                break
    except SyntaxError as e:
        # Если есть синтаксическая ошибка, добавляем её в результаты
        results.append(f"Ошибка: {str(e)}")
        all_tests_passed = False
    except Exception as e:
        # Если произошла другая ошибка, добавляем её в результаты
        results.append(f"Ошибка: {str(e)}")
        all_tests_passed = False
        
    if all_tests_passed:
        status = "completed"
    else:
        status = "in_progress"
    
    update_user_progress(
        login=login,  
        block_id=block_id,
        task_id=task_id,
        status=status
    )
    # Возвращаем результаты на страницу
    return templates.TemplateResponse(
        "task.html",
        {
            "request": request,
            "block_name": task["block_name"],
            "task_name": task["tasks"][0]["task_name"],
            "task_description": task["tasks"][0]["task_description"],
            "task_id": task["tasks"][0]["task_id"],
            "test_cases": test_cases,
            "code": code,
            "results": results,
            "all_tests_passed": all_tests_passed,  # Передаем результат проверки
            "code_submitted": True  # Флаг, указывающий, что код был отправлен
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)