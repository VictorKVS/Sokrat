"""
Тесты для Базы Знаний (асинхронная версия).
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

class TestKnowledgeBase:
    """
    Асинхронные тесты для KnowledgeBase.
    """
    
    def setup_method(self):
        """Подготовка перед каждым тестом"""
        self.test_db = "test_sokrat.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    @pytest.mark.asyncio
    async def test_1_database_initialization(self):
        """ТЕСТ: Проверяем инициализацию БД."""
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        assert os.path.exists(self.test_db), "БД не создалась"
        
        import aiosqlite
        async with aiosqlite.connect(self.test_db) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            tables = [row[0] async for row in cursor]
            
            expected_tables = [
                'research_sessions',
                'research_rounds',
                'expertise_results'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Таблица {table} не создана"
    
    @pytest.mark.asyncio
    async def test_2_save_and_get_session(self):
        """ТЕСТ: Сохранение и получение сессии."""
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        session_id = "test-session-123"
        task = "Напиши функцию сортировки"
        config = {
            "initial_prompt": "Используй быструю сортировку",
            "max_rounds": 3,
            "models": ["gpt-4", "claude"]
        }
        
        await kb.save_session(session_id, task, config)
        history = await kb.get_session_history(session_id)
        
        assert history['session'] is not None, "Сессия не найдена"
        assert history['session'][1] == task, "Задача не совпадает"
        
        import json
        saved_config = json.loads(history['session'][2])
        assert saved_config['initial_prompt'] == config['initial_prompt'], "Конфиг не совпадает"
    
    @pytest.mark.asyncio
    async def test_3_save_and_get_expertise(self):
        """ТЕСТ: Сохранение результатов экспертизы."""
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        session_id = "test-session-456"
        await kb.save_session(session_id, "Тестовая задача", {})
        
        expertise_data = [
            ("code", ["баг1", "баг2"], ["фикс1"], 7.5),
            ("prompt", ["нечётко"], ["уточнить"], 8.0),
            ("analytics", ["ошибка"], ["проверить"], 6.0)
        ]
        
        for i, (exp_type, findings, suggestions, score) in enumerate(expertise_data):
            await kb.save_expertise(
                session_id=session_id,
                round_number=i,
                expert_type=exp_type,
                findings=findings,
                suggestions=suggestions,
                score=score
            )
        
        history = await kb.get_session_history(session_id)
        assert len(history['expertise']) == 3, f"Ожидалось 3 экспертизы, получено {len(history['expertise'])}"
        
        exp = history['expertise'][0]
        import json
        findings = json.loads(exp[4])
        assert "баг1" in findings, "Findings не сохранились"
    
    @pytest.mark.asyncio
    async def test_4_save_and_get_round(self):
        """ТЕСТ: Сохранение раундов исследования."""
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        session_id = "test-session-789"
        await kb.save_session(session_id, "Тест раундов", {})
        
        rounds = [
            {"type": "primary", "content": "Первый ответ", "model": "gpt-4"},
            {"type": "discussion", "responses": {"gpt": "ответ1", "claude": "ответ2"}},
            {"type": "final", "synthesis": "Итоговый ответ", "score": 8.5}
        ]
        
        for i, round_data in enumerate(rounds):
            await kb.save_round(session_id, i, round_data)
        
        history = await kb.get_session_history(session_id)
        assert len(history['rounds']) == 3, f"Ожидалось 3 раунда, получено {len(history['rounds'])}"
        
        import json
        first_round = json.loads(history['rounds'][0][3])
        assert first_round['type'] == 'primary', "Первый раунд не primary"
    
    @pytest.mark.asyncio
    async def test_5_error_handling(self):
        """ТЕСТ: Обработка ошибок - несуществующая сессия."""
        from knowledge_base import KnowledgeBase
        
        kb = KnowledgeBase(db_path=self.test_db)
        await kb._init_db()
        
        # Запрос несуществующей сессии должен вернуть пустые списки, а не упасть
        history = await kb.get_session_history("non-existent")
        assert history['session'] is None, "Должен быть None для несуществующей сессии"
        assert isinstance(history['rounds'], list), "rounds должен быть списком"
        assert len(history['rounds']) == 0, "rounds должен быть пустым"
        assert isinstance(history['expertise'], list), "expertise должен быть списком"
        assert len(history['expertise']) == 0, "expertise должен быть пустым"
        
        # Проверяем что сессия не существует
        exists = await kb.session_exists("non-existent")
        assert not exists, "session_exists должен вернуть False"
        
        # Удаление несуществующей сессии не должно падать
        await kb.delete_session("non-existent")
        print(" Обработка ошибок работает корректно")
