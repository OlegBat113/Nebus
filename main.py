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

app = FastAPI()

# Настройка статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
