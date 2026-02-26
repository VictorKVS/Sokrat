import asyncio
import uuid
from typing import Dict, Any

from src.core.search import search_web
from src.core.parser import parse_urls
from src.core.cleaner import clean_documents
from src.core.dispatcher import dispatch_to_models
from src.db import crud
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class AnalysisOrchestrator:
    async def run_analysis(self, query: str) -> Dict[str, Any]:
        query_id = str(uuid.uuid4())
        logger.info(f" Старт анализа [{query_id}]: {query}")
        
        try:
            # 1. Сохраняем запрос
            await crud.create_query(query_id, query)
            
            # 2. Поиск
            logger.info(" Поиск в интернете...")
            search_results = await search_web(query)
            await crud.save_sources(query_id, search_results)
            logger.info(f" Найдено {len(search_results)} источников")
            
            if not search_results:
                return {
                    "query_id": query_id,
                    "sources": [],
                    "model_analyses": {},
                    "confidence_flags": [" Не найдено источников"]
                }
            
            # 3. Парсинг
            logger.info(" Парсинг страниц...")
            urls = [r["url"] for r in search_results]
            parsed_docs = await parse_urls(urls)
            
            if not parsed_docs:
                return {
                    "query_id": query_id,
                    "sources": [{"url": r["url"], "title": r["title"]} for r in search_results],
                    "model_analyses": {},
                    "confidence_flags": [" Не удалось распарсить страницы"]
                }
            
            # 4. Очистка
            logger.info(" Очистка текста...")
            cleaned_docs = clean_documents(parsed_docs)
            await crud.save_documents(query_id, cleaned_docs)
            
            # 5. Подготовка контекста
            combined_text = "\n\n---\n\n".join([
                f"[{doc['title']}]({doc['url']})\n{doc['cleaned_text'][:5000]}"
                for doc in cleaned_docs
            ])
            
            # 6. Отправка моделям
            logger.info(" Отправка запросов к моделям...")
            model_responses = await dispatch_to_models(query_id, combined_text)
            
            # 7. Результат
            result = {
                "query_id": query_id,
                "sources": [
                    {"url": doc["url"], "title": doc["title"]}
                    for doc in cleaned_docs
                ],
                "model_analyses": model_responses,
                "confidence_flags": self._check_confidence(model_responses)
            }
            
            logger.info(" Анализ успешно завершён")
            return result
            
        except Exception as e:
            logger.error(f" Критическая ошибка: {str(e)}")
            return {
                "query_id": query_id,
                "sources": [],
                "model_analyses": {},
                "confidence_flags": [f" Ошибка: {str(e)[:100]}"]
            }
    
    def _check_confidence(self, responses):
        flags = []
        for model, resp in responses.items():
            if "недостаточно данных" in resp.lower():
                flags.append(f"{model}: недостаточно данных")
            if "нет данных" in resp.lower():
                flags.append(f"{model}: нет данных в источниках")
            if "ERROR" in resp:
                flags.append(f"{model}: ошибка вызова")
        return flags
