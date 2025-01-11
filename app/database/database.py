from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

DATABASE_URL = "postgresql://user:password@localhost/dbname"  # Замените на ваш URL базы данных

# Создание асинхронного подключения к базе данных
database = Database(DATABASE_URL)

Base = declarative_base()

# Функция для получения сессии базы данных
async def get_db():
    async with database.transaction():
        yield database
