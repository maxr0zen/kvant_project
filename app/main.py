from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db.mongodb import get_user_by_login
from pymongo import MongoClient
import logging

app = FastAPI()

# Настройка Jinja2
templates = Jinja2Templates(directory="templates")

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["kvant_users"]
blocks_collection = db["blocks"]

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Маршрут для отображения страницы авторизации
@app.get("/", response_class=HTMLResponse)
async def read_login_page(request: Request):
    logger.info("Отображение страницы авторизации")
    return templates.TemplateResponse("login.html", {"request": request})

# Маршрут для обработки данных из формы
@app.post("/login")
async def login(request: Request, login: str = Form(...), password: str = Form(...)):
    logger.info(f"Попытка авторизации: login={login}, password={password}")
    user = get_user_by_login(login)
    
    if user and user['password'] == password:
        logger.info("Авторизация успешна, перенаправление на /dashboard")
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        logger.warning("Неверный логин или пароль")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

# Маршрут для отображения страницы после успешной авторизации
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard_page(request: Request):
    logger.info("Отображение страницы dashboard")
    
    # Получаем все блоки заданий из MongoDB
    blocks = list(blocks_collection.find({}))
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "blocks": blocks  # Передаем блоки в шаблон
        }
    )