from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.database import AsyncSessionLocal
from src.db.models import Query, Source, Document, ModelCall
from datetime import datetime
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def create_query(query_id: str, query_text: str):
    """Создать запись о запросе"""
    async with AsyncSessionLocal() as session:
        query = Query(
            id=query_id,
            query_text=query_text,
            timestamp=datetime.utcnow()
        )
        session.add(query)
        await session.commit()
    logger.debug(f"Query saved: {query_id}")

async def save_sources(query_id: str, sources: list):
    """Сохранить найденные источники"""
    async with AsyncSessionLocal() as session:
        for src in sources:
            source = Source(
                query_id=query_id,
                url=src["url"],
                title=src["title"],
                snippet=src["snippet"],
                rank=src["rank"]
            )
            session.add(source)
        await session.commit()
    logger.debug(f"Saved {len(sources)} sources for query {query_id}")

async def save_documents(query_id: str, documents: list):
    """Сохранить распарсенные документы с raw_html"""
    async with AsyncSessionLocal() as session:
        for doc in documents:
            # Находим source по url
            result = await session.execute(
                select(Source).where(Source.url == doc["url"])
            )
            source = result.scalar_one()
            
            document = Document(
                source_id=source.id,
                cleaned_text=doc["cleaned_text"],
                raw_html=doc.get("raw_html", ""),  # Добавлено
                word_count=doc["word_count"]
            )
            session.add(document)
        await session.commit()
    logger.debug(f"Saved {len(documents)} documents for query {query_id}")

async def save_model_call(call_data: dict):
    """Сохранить вызов модели с токенами"""
    async with AsyncSessionLocal() as session:
        call = ModelCall(
            query_id=call_data["query_id"],
            model_name=call_data["model_name"],
            prompt=call_data["prompt"],
            response=call_data["response"],
            prompt_tokens=call_data.get("prompt_tokens"),  # Добавлено
            completion_tokens=call_data.get("completion_tokens"),  # Добавлено
            total_tokens=call_data.get("total_tokens"),  # Добавлено
            response_time_ms=call_data.get("response_time_ms"),
            status=call_data["status"],
            error_message=call_data.get("error_message")
        )
        session.add(call)
        await session.commit()
    logger.debug(f"Saved model call for {call_data['model_name']}")

async def get_query_stats(query_id: str):
    """Получить статистику по запросу (для проверки)"""
    async with AsyncSessionLocal() as session:
        # Получаем запрос
        query_result = await session.execute(
            select(Query).where(Query.id == query_id)
        )
        query = query_result.scalar_one()
        
        # Получаем источники
        sources_result = await session.execute(
            select(Source).where(Source.query_id == query_id)
        )
        sources = sources_result.scalars().all()
        
        # Получаем вызовы моделей
        calls_result = await session.execute(
            select(ModelCall).where(ModelCall.query_id == query_id)
        )
        calls = calls_result.scalars().all()
        
        return {
            "query": query.query_text,
            "sources_count": len(sources),
            "model_calls_count": len(calls),
            "total_tokens": sum(c.total_tokens or 0 for c in calls)
        }
