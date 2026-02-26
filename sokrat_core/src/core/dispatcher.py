import httpx
import asyncio
from typing import Dict
from src.config import settings
from src.db import crud
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def dispatch_to_models(query_id: str, context: str) -> Dict[str, str]:
    """Отправка контекста всем моделям параллельно"""
    
    prompt_template = """На основе следующего материала:
{context}

Выполни строгий анализ:

1. Ключевые технические параметры (только из текста):
   - Извлеки числовые значения, единицы измерения
   - Укажи технические характеристики, если есть

2. Недостающие данные:
   - Что из важного не указано в тексте?
   - Какие параметры требуют уточнения?

3. Источники неопределённости:
   - Какие утверждения требуют проверки?
   - Где возможны ошибки?

ВАЖНО: 
- Используй ТОЛЬКО информацию из предоставленного текста
- Не добавляй свои знания
- Если данных нет  напиши "нет данных в источнике"
"""

    async def call_model(model_name: str) -> tuple:
        start_time = asyncio.get_event_loop().time()
        
        prompt = prompt_template.format(context=context[:10000])
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Ты аналитик, работающий строго по тексту. Не выдумывай."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        # Если нет ключа OpenRouter - возвращаем заглушку
        if not settings.openrouter_api_key or settings.openrouter_api_key == "your-openrouter-key-here":
            mock_response = f"[MOCK] Анализ от {model_name}\n\nКлючевые параметры: 45% эффективность\nНедостающие данные: стоимость, срок службы\nНеопределённость: зависит от погодных условий"
            
            # Логируем заглушку
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            await crud.save_model_call({
                "query_id": query_id,
                "model_name": model_name,
                "prompt": prompt,
                "response": mock_response,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "response_time_ms": int(elapsed),
                "status": "success"
            })
            
            return model_name, mock_response
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                result = data["choices"][0]["message"]["content"]
                
                # Получаем токены
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                # Логируем
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                await crud.save_model_call({
                    "query_id": query_id,
                    "model_name": model_name,
                    "prompt": prompt,
                    "response": result,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "response_time_ms": int(elapsed),
                    "status": "success"
                })
                
                logger.info(f" {model_name} ответил за {int(elapsed)}ms, токенов: {total_tokens}")
                return model_name, result
                
        except Exception as e:
            logger.error(f" {model_name} ошибка: {str(e)}")
            
            await crud.save_model_call({
                "query_id": query_id,
                "model_name": model_name,
                "prompt": prompt,
                "response": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "status": "error",
                "error_message": str(e)
            })
            
            return model_name, f"[ERROR: {model_name} failed]"
    
    # Запускаем все модели параллельно
    tasks = [call_model(model) for model in settings.models]
    results = await asyncio.gather(*tasks)
    
    return dict(results)
