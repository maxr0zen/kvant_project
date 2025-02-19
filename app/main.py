from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db.mongodb import get_user_by_login

app = FastAPI()

# Настройка Jinja2
templates = Jinja2Templates(directory="templates")

# Маршрут для отображения страницы авторизации
@app.get("/", response_class=HTMLResponse)
async def read_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Маршрут для обработки данных из формы
@app.post("/login")
async def login(request: Request, login: str = Form(...), password: str = Form(...)):
    user = get_user_by_login(login)
    
    if user and user['password'] == password:
        # Перенаправление на страницу dashboard при успешной авторизации
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        # Возврат на страницу авторизации с сообщением об ошибке
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

# Маршрут для отображения страницы после успешной авторизации
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})