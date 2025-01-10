 # main.py

from fastapi import FastAPI
from app.routes import routers
from app.database import engine, Base
import uvicorn

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(routers.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
