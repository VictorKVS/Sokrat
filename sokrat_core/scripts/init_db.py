import asyncio
import sys
import os

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db.database import init_db, engine
from src.utils.logging_config import get_logger
from sqlalchemy import inspect

logger = get_logger(__name__)

async def main():
    logger.info(" Инициализация базы данных...")
    await init_db()
    logger.info(" База данных готова")

    # Проверяем созданные таблицы
    try:
        async with engine.connect() as conn:
            # Получаем таблицы через асинхронный run_sync
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
            if tables:
                logger.info(f" Созданы таблицы: {', '.join(tables)}")
            else:
                logger.warning(" Таблицы не найдены")
    except Exception as e:
        logger.error(f" Ошибка при проверке таблиц: {e}")

if __name__ == "__main__":
    asyncio.run(main())
