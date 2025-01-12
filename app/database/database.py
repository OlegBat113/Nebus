from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./test.db"  # Замените на ваш URL базы данных

# Создание движка базы данных
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создание сессии базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db() -> Session:
    db: Session = SessionLocal()
    try:
        #yield db
        return db
    finally:
        db.close()
