

Вот пошаговая инструкция по созданию проекта с использованием FastAPI, Pydantic, SQLAlchemy, Alembic и SQLite.

### Шаг 1: Установка зависимостей

Создайте новую папку для вашего проекта и перейдите в нее. Затем создайте виртуальное окружение и установите необходимые пакеты:

```bash
mkdir my_fastapi_project
cd my_fastapi_project
python -m venv venv
source venv/bin/activate  # Для Windows используйте venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy alembic pydantic
```

### Шаг 2: Структура проекта

Рекомендуемая структура проекта:

```
your_project/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── routers.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── alembic/
│       ├── env.py
│       └── versions/
│           └── (ваши миграции)
│
├── alembic.ini
├── requirements.txt
├── .env
└── README.md
```

### Шаг 3: Настройка базы данных

Создайте файл `database.py` для настройки SQLAlchemy и Alembic:

```python:app/database.py
# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### Шаг 4: Создание моделей

Создайте файл `models.py` для определения моделей:

```python:app/models.py
# app/models.py

from sqlalchemy import Column, Integer, String
from .database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
```

### Шаг 5: Создание схем

Создайте файл `schemas.py` для определения Pydantic схем:

```python:app/schemas.py
# app/schemas.py

from pydantic import BaseModel

class ItemBase(BaseModel):
    name: str
    description: str

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True
```

### Шаг 6: Создание маршрутов

Создайте файл `items.py` для определения маршрутов:

```python:app/routes/items.py
# app/routes/items.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

### Шаг 7: Настройка Alembic

Создайте файл `alembic.ini` и настройте его для работы с SQLite. Убедитесь, что строка `sqlalchemy.url` указывает на вашу базу данных:

```ini
# alembic.ini

[alembic]
script_location = alembic
# Убедитесь, что эта строка указывает на вашу базу данных
sqlalchemy.url = sqlite:///./test.db
```

Инициализируйте Alembic:

```bash
alembic init alembic
```

### Шаг 8: Создание миграции

Создайте миграцию для вашей модели:

```bash
alembic revision --autogenerate -m "Initial migration"
```

Примените миграцию:

```bash
alembic upgrade head
```

### Шаг 9: Обновление `main.py`

Создайте файл `main.py` для запуска приложения:

```python:app/main.py
# app/main.py

from fastapi import FastAPI
from app.routes import items
from app.database import engine, Base

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### Шаг 10: Запуск приложения

Запустите приложение с помощью Uvicorn:

```bash
uvicorn app.main:app --reload
```

Теперь ваше FastAPI приложение с использованием Pydantic, SQLAlchemy, Alembic и SQLite готово к работе! Вы можете отправлять запросы к маршруту `/items/` для создания новых элементов.

-----------------------------------------------------------------------------
При редактировании, добавлении, удалении моделей, необходимо:

2. Обновите файл миграции
После добавления новой модели вам нужно создать миграцию для обновления базы данных. Запустите следующую команду в терминале:
alembic revision --autogenerate -m "Добавление таблицы Building"

3. Примените миграцию
После создания миграции примените ее с помощью команды:
alembic upgrade head
-----------------------------------------------------------------------------
