"""
Тестовый запуск Research Engine.
"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем пути
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from research_engine.core.models import SessionContext
from research_engine.core.orchestrator import ResearchOrchestrator
from knowledge_base import KnowledgeBase

async def main():
    print("="*60)
    print(" SOKRAT RESEARCH ENGINE v0.1")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Инициализация
    print(" Инициализация Базы Знаний...")
    kb = KnowledgeBase()
    
    print(" Инициализация Оркестратора...")
    orchestrator = ResearchOrchestrator(kb_client=kb)
    
    # Создаём контекст
    context = SessionContext(
        task="Напиши эффективную функцию сортировки на Python",
        initial_prompt="Используй алгоритм быстрой сортировки, оптимизируй для больших данных",
        rag_context="Для сортировки больших данных учитывай использование памяти O(log n)",
        negative_constraints="НЕ используй встроенную sort(), НЕ используй рекурсию если глубина >1000",
        max_rounds=3
    )
    
    print(f"\n Сессия: {context.session_id}")
    print(f" Задача: {context.task}")
    print(f" Макс. раундов: {context.max_rounds}")
    print()
    
    # Запускаем
    print(" Запуск исследования...")
    print("-" * 40)
    
    result = await orchestrator.run(context)
    
    print("-" * 40)
    print("\n ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print(f" Итоговая оценка: {result.quality_score}/10")
    print(f" Тренд улучшений: {result.improvement_trend}")
    print(f"\n ФИНАЛЬНЫЙ ОТВЕТ:")
    print("-" * 40)
    print(result.final_synthesis)
    print("=" * 60)
    
    # Проверяем БД
    print("\n СТАТИСТИКА БАЗЫ ЗНАНИЙ:")
    history = kb.get_session_history(result.session_id)
    print(f"   Сессия: {'' if history['session'] else ''}")
    print(f"   Раундов: {len(history['rounds'])}")
    print(f"   Экспертиз: {len(history['expertise'])}")
    
    # Показываем содержимое
    if history['expertise']:
        print("\n РЕЗУЛЬТАТЫ ЭКСПЕРТИЗ:")
        for exp in history['expertise']:
            print(f"   {exp[3]}: оценка {exp[6]}/10")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
