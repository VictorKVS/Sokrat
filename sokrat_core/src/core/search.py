import httpx
from typing import List, Dict
from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def search_web(query: str) -> List[Dict]:
    """Поиск через Tavily API"""
    
    # Если нет ключа - возвращаем тестовые данные
    if not settings.tavily_api_key or settings.tavily_api_key == "your-tavily-key-here":
        logger.warning(" Tavily API key not set, using mock data")
        return [
            {
                "url": "https://example.com/1",
                "title": "Wave Energy Efficiency Study",
                "snippet": "Wave energy conversion efficiency ranges from 40-60%...",
                "rank": 1
            },
            {
                "url": "https://example.com/2",
                "title": "Coastal Wave Power Plants",
                "snippet": "Near-shore wave energy converters achieve 35-45% efficiency...",
                "rank": 2
            }
        ]
    
    exclude_domains = [
        "forum", "reddit.com", "quora.com", 
        "youtube.com", "facebook.com", "twitter.com"
    ]
    
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": settings.max_search_results,
        "exclude_domains": exclude_domains,
        "include_answer": False,
        "include_raw_content": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.search_timeout) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for idx, result in enumerate(data.get("results", [])):
                results.append({
                    "url": result["url"],
                    "title": result["title"],
                    "snippet": result.get("content", "")[:500],
                    "rank": idx + 1
                })
            
            logger.info(f" Найдено {len(results)} результатов")
            return results
            
    except Exception as e:
        logger.error(f" Ошибка поиска: {str(e)}")
        return []
