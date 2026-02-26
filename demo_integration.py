#!/usr/bin/env python
"""
Демонстрация полной системы: Research Engine + Knowledge Base.
"""
import asyncio
import os
import sys
from datetime import datetime

# Добавляем пути
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from research_engine.core.models import SessionContext
from research_engine.core.orchestrator import ResearchOrchestrator
from knowledge_base import KnowledgeBase

async def main():
    print("="*60)
    print(" SOKRAT RESEARCH SYSTEM - ПОЛНАЯ ИНТЕГРАЦИЯ")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Инициализация
    print(" Инициализация Базы Знаний...")
    kb = KnowledgeBase(db_path="data/sokrat_research.db")
    await kb._init_db()
    
    print(" Инициализация Research Engine...")
    orchestrator = ResearchOrchestrator(kb_client=kb)
    
    # 2. Создаём задачу
    print("\n СОЗДАНИЕ ЗАДАЧИ")
    print("-" * 40)
    
    context = SessionContext(
        task="Напиши эффективную функцию сортировки на Python",
        initial_prompt="Используй алгоритм быстрой сортировки, оптимизируй для больших данных",
        rag_context="Для сортировки больших данных учитывай использование памяти O(log n)",
        negative_constraints="НЕ используй встроенную sort()",
        max_rounds=2
    )
    
    print(f" Сессия: {context.session_id}")
    print(f" Задача: {context.task}")
    print(f" Макс. раундов: {context.max_rounds}")
    print()
    
    # 3. Запуск исследования
    print(" ЗАПУСК ИССЛЕДОВАНИЯ")
    print("-" * 40)
    
    result = await orchestrator.run(context)
    
    # 4. Результаты
    print("\n ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 40)
    print(f" Итоговая оценка: {result.quality_score}/10")
    print(f" Тренд: {result.improvement_trend}")
    
    print("\n ФИНАЛЬНЫЙ ОТВЕТ:")
    print("-" * 40)
    if result.final_synthesis:
        print(result.final_synthesis[:500] + "..." if len(result.final_synthesis) > 500 else result.final_synthesis)
    
    # 5. Статистика из БД (ВАЖНО: добавляем await!)
    print("\n СТАТИСТИКА ИЗ БАЗЫ ЗНАНИЙ")
    print("-" * 40)
    
    history = await kb.get_session_history(result.session_id)
    
    # Проверяем что получили данные
    if history['session']:
        session_data = history['session']
        print(f" Сессия: {session_data[0]}")  # id
        print(f" Задача: {session_data[1][:50]}...")  # task
        print(f" Создана: {session_data[3]}")  # created_at
    else:
        print(" Сессия не найдена в БД")
    
    print(f" Раундов: {len(history['rounds'])}")
    print(f" Экспертиз: {len(history['expertise'])}")
    
    # Показываем экспертизы
    if history['expertise']:
        print("\n РЕЗУЛЬТАТЫ ЭКСПЕРТИЗ:")
        for exp in history['expertise'][:3]:
            print(f"   {exp[3]}: оценка {exp[6]}/10")
            import json
            findings = json.loads(exp[4])
            if findings:
                print(f"    Найдено: {', '.join(findings[:2])}")
    
    # 6. Все сессии
    print("\n ВСЕ СЕССИИ В БАЗЕ:")
    all_sessions = await kb.get_all_sessions(5)
    for s in all_sessions:
        print(f"   {s[0][:8]}...: {s[1][:50]}... ({s[2][:10]})")
    
    print("\n" + "="*60)
    print(" СИСТЕМА РАБОТАЕТ ПОЛНОСТЬЮ")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
