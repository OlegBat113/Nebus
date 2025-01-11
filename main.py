# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import fastapi
#from fastapi.templating import Jinja2Templates
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

# Настройка шаблонов Jinja2
templates = fastapi.templating.Jinja2Templates(directory="templates")

app.include_router(router)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
