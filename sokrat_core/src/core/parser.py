import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import asyncio
from src.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def parse_urls(urls: List[str]) -> List[Dict]:
    """Параллельный парсинг страниц"""
    
    async def fetch_and_parse(url: str):
        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout,
                follow_redirects=True,
                headers={"User-Agent": settings.user_agent}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Проверка типа контента
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return None
                
                # Сохраняем raw_html (обрезаем если слишком большой)
                raw_html = response.text[:50000]  # Ограничим 50KB для БД
                
                # Парсинг
                soup = BeautifulSoup(response.text, "lxml")
                
                # Удаляем мусор
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                    tag.decompose()
                
                # Извлекаем основной контент
                main_content = soup.find("main") or soup.find("article") or soup.body
                if not main_content:
                    main_content = soup
                
                text = main_content.get_text(separator="\n", strip=True)
                
                # Обрезаем если слишком длинно
                if len(text) > settings.max_page_size_chars:
                    text = text[:settings.max_page_size_chars] + "...[truncated]"
                
                return {
                    "url": url,
                    "title": soup.title.string if soup.title else url,
                    "cleaned_text": text,
                    "raw_html": raw_html,
                    "word_count": len(text.split())
                }
                
        except Exception as e:
            logger.warning(f" Ошибка парсинга {url}: {str(e)}")
            return None
    
    # Ограничиваем параллельные запросы
    semaphore = asyncio.Semaphore(3)
    
    async def bounded_fetch(url):
        async with semaphore:
            return await fetch_and_parse(url)
    
    tasks = [bounded_fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    valid_docs = [r for r in results if r is not None]
    logger.info(f" Успешно спарсено {len(valid_docs)}/{len(urls)} страниц")
    
    return valid_docs
