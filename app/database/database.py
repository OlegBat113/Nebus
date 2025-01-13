from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Iterator
DATABASE_URL = "sqlite:///./test.db"  # Замените на ваш URL базы данных

# Создание движка базы данных
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создание сессии базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    # type(db)=<class 'sqlalchemy.orm.session.Session'>
    print(f"-> get_db() -> db={type(db)} ...")
    try:
        yield db
        #return db  # Return the session directly
    finally:
        db.close()
