import re
from typing import List, Dict
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def clean_documents(documents: List[Dict]) -> List[Dict]:
    """Очистка и нормализация текста"""
    
    cleaned = []
    for doc in documents:
        text = doc["cleaned_text"]
        
        # Убираем лишние переносы
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Убираем повторы (простая версия)
        lines = text.split("\n")
        unique_lines = []
        seen = set()
        
        for line in lines:
            line = line.strip()
            if len(line) < 50 and line in seen:
                continue
            if line:
                seen.add(line[:50])
                unique_lines.append(line)
        
        # Собираем обратно
        text = "\n".join(unique_lines)
        
        # Разбиваем на абзацы
        paragraphs = text.split("\n\n")
        
        # Фильтруем абзацы: убираем слишком короткие (< 50 символов без смысла)
        meaningful = []
        for p in paragraphs:
            # Убираем абзацы короче 50 символов (если это не число или спецсимвол)
            if len(p) < 50 and not re.search(r'\d+%|\d+\s*(kW|MW|kWh)', p):
                continue
            # Убираем абзацы, где меньше 5 слов
            if len(p.split()) < 5:
                continue
            meaningful.append(p)
        
        # Приводим единицы измерения к стандарту
        text = "\n\n".join(meaningful)
        text = re.sub(r'(\d+)\s*м\b', r'\1 meters', text)
        text = re.sub(r'(\d+)\s*км\b', r'\1 kilometers', text)
        text = re.sub(r'(\d+)\s*кВт\b', r'\1 kW', text)
        text = re.sub(r'(\d+)\s*МВт\b', r'\1 MW', text)
        text = re.sub(r'(\d+)\s*кВтч\b', r'\1 kWh', text)
        
        doc["cleaned_text"] = text
        doc["word_count"] = len(text.split())
        
        cleaned.append(doc)
    
    logger.info(f" Очищено {len(cleaned)} документов")
    return cleaned
