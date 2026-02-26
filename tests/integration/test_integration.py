"""
Интеграционные тесты: Research Engine + Knowledge Base.
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from research_engine.core.models import SessionContext
from research_engine.core.orchestrator import ResearchOrchestrator
from knowledge_base import KnowledgeBase

class TestIntegration:
    """
    Тестируем совместную работу Research Engine и Knowledge Base.
    """
    
    def setup_method(self):
        """Подготовка перед каждым тестом"""
        self.test_db = "test_integration.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    @pytest.mark.asyncio
    async def test_1_full_research_cycle(self):
        """
        ТЕСТ: Полный цикл исследования с сохранением в БД.
        """
        # Инициализация
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        orchestrator = ResearchOrchestrator(kb_client=kb)
        
        # Создаём контекст
        context = SessionContext(
            task="Тестовая задача для интеграции",
            initial_prompt="Напиши функцию на Python",
            max_rounds=1
        )
        
        # Запускаем исследование
        result = await orchestrator.run(context)
        
        # Проверяем что сессия сохранилась
        history = await kb.get_session_history(result.session_id)
        assert history['session'] is not None, "Сессия не сохранилась"
        assert len(history['expertise']) > 0, "Экспертизы не сохранились"
        assert len(history['rounds']) > 0, "Раунды не сохранились"
        
        print(f"\n Интеграция работает:")
        print(f"   Сессия: {result.session_id}")
        print(f"   Экспертиз: {len(history['expertise'])}")
        print(f"   Раундов: {len(history['rounds'])}")
        print(f"   Оценка: {result.quality_score}/10")
    
    @pytest.mark.asyncio
    async def test_2_multiple_sessions(self):
        """
        ТЕСТ: Несколько сессий в одной БД.
        """
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        orchestrator = ResearchOrchestrator(kb_client=kb)
        
        sessions = []
        for i in range(3):
            context = SessionContext(
                task=f"Тестовая задача {i}",
                initial_prompt="Тест",
                max_rounds=1
            )
            result = await orchestrator.run(context)
            sessions.append(result.session_id)
        
        # Проверяем что все сессии сохранились
        all_sessions = await kb.get_all_sessions()
        assert len(all_sessions) == 3, f"Ожидалось 3 сессии, получено {len(all_sessions)}"
        
        print(f"\n Множественные сессии:")
        for s in all_sessions:
            print(f"   {s[0][:8]}...: {s[1][:30]}...")
    
    @pytest.mark.asyncio
    async def test_3_recover_session(self):
        """
        ТЕСТ: Восстановление сессии из БД.
        """
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        orchestrator = ResearchOrchestrator(kb_client=kb)
        
        # Создаём сессию
        context = SessionContext(
            task="Тест восстановления",
            initial_prompt="Тест",
            max_rounds=2
        )
        result = await orchestrator.run(context)
        session_id = result.session_id
        
        # Получаем историю из БД
        history = await kb.get_session_history(session_id)
        
        # Проверяем что можем восстановить данные
        assert history['session'][1] == "Тест восстановления", "Задача не совпадает"
        
        print(f"\n Восстановление работает:")
        print(f"   Сессия восстановлена: {session_id}")
        print(f"   Раундов в истории: {len(history['rounds'])}")
