# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import fastapi.templating

from app.routes.router import router
from app.database.database import engine, Base
import uvicorn

# Создание таблиц
Base.metadata.create_all(bind=engine)

# объект FastAPI
app = FastAPI()

# Настройка статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключение маршрутов
app.include_router(router)

# Запуск сервера
#if __name__ == "__main__":
#    uvicorn.run("main:app", reload=True, , host="0.0.0.0")


# Запуск сервера в Docker
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload


