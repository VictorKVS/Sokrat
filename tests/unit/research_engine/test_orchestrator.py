"""
Тесты для Research Engine.
Определяем желаемое поведение оркестратора.
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

class TestResearchOrchestrator:
    """
    Тесты для ResearchOrchestrator.
    Определяем как должен работать оркестратор.
    """
    
    @pytest.mark.asyncio
    async def test_1_create_session_context(self):
        """
        ТЕСТ: Создание контекста сессии.
        
        Хотим:
        1. Контекст создаётся с правильными полями
        2. session_id генерируется автоматически
        3. Все поля инициализируются
        """
        from research_engine.core.models import SessionContext
        
        context = SessionContext(
            task="Тестовая задача",
            initial_prompt="Тестовый промпт"
        )
        
        assert context.session_id is not None, "session_id не сгенерирован"
        assert context.task == "Тестовая задача", "task не сохранился"
        assert context.current_round == 0, "current_round должен быть 0"
        assert isinstance(context.expertise_results, list), "expertise_results должен быть списком"
        assert isinstance(context.discussion_rounds, list), "discussion_rounds должен быть списком"
    
    @pytest.mark.asyncio
    async def test_2_orchestrator_run_with_mocks(self):
        """
        ТЕСТ: Запуск оркестратора с заглушками.
        
        Хотим:
        1. Оркестратор запускается без ошибок
        2. Возвращает результат
        3. Проходит все этапы
        """
        from research_engine.core.models import SessionContext
        from research_engine.core.orchestrator import ResearchOrchestrator
        
        # Создаём заглушки для теста
        class MockKB:
            async def save_session(self, *args, **kwargs):
                pass
            async def save_round(self, *args, **kwargs):
                pass
            async def save_expertise(self, *args, **kwargs):
                pass
        
        orchestrator = ResearchOrchestrator(kb_client=MockKB())
        
        context = SessionContext(
            task="Тестовая задача",
            initial_prompt="Тестовый промпт"
        )
        
        result = await orchestrator.run(context)
        
        assert result is not None, "Оркестратор не вернул результат"
        assert result.is_finished, "Исследование не завершилось"
        assert result.quality_score > 0, "Оценка не выставлена"
    
    @pytest.mark.asyncio
    async def test_3_expertise_round_parallel(self):
        """
        ТЕСТ: Экспертизы запускаются параллельно.
        
        Хотим:
        1. Все три экспертизы запускаются одновременно
        2. Результаты собираются вместе
        3. Время выполнения меньше суммы по отдельности
        """
        from research_engine.core.models import SessionContext
        from research_engine.core.orchestrator import ResearchOrchestrator
        
        orchestrator = ResearchOrchestrator()
        
        import time
        start = time.time()
        
        # Запускаем экспертизы
        results = await orchestrator._run_expertise_round("Тестовый контент")
        
        elapsed = time.time() - start
        
        assert len(results) == 3, f"Ожидалось 3 результата, получено {len(results)}"
        
        # Проверяем что все три типа есть
        types = [r.expert_type for r in results]
        assert "code" in types, "Нет эксперта по коду"
        assert "prompt" in types, "Нет эксперта по промптам"
        assert "analytics" in types, "Нет эксперта по аналитике"
        
        # Проверяем что выполнялось параллельно
        # (каждый эксперт спит 0.5 сек, параллельно = ~0.5 сек, последовательно = 1.5 сек)
        assert elapsed < 1.0, f"Слишком долго: {elapsed} сек, вероятно не параллельно"
    
    @pytest.mark.asyncio
    async def test_4_discussion_round(self):
        """
        ТЕСТ: Круг обсуждения.
        
        Хотим:
        1. Обсуждение возвращает ответы от нескольких моделей
        2. Есть структура с responses
        """
        from research_engine.core.models import SessionContext
        from research_engine.core.orchestrator import ResearchOrchestrator
        
        orchestrator = ResearchOrchestrator()
        
        context = SessionContext(
            task="Тест",
            initial_prompt="тест"
        )
        
        discussion = await orchestrator._run_discussion_round(context)
        
        assert discussion.round_number > 0, "Номер раунда не установлен"
        assert len(discussion.responses) > 0, "Нет ответов от моделей"
        assert "gpt-4" in discussion.responses, "Нет ответа от GPT"
    
    @pytest.mark.asyncio
    async def test_5_judge_decision(self):
        """
        ТЕСТ: Судья принимает решение.
        
        Хотим:
        1. Судья возвращает структурированное решение
        2. Есть все поля: should_stop, reason, score
        3. Решение логично
        """
        from research_engine.core.models import SessionContext
        from research_engine.core.orchestrator import ResearchOrchestrator
        
        orchestrator = ResearchOrchestrator()
        
        context = SessionContext(
            task="Тест",
            initial_prompt="тест"
        )
        
        decision = await orchestrator._run_judge(context)
        
        assert hasattr(decision, 'should_stop'), "Нет should_stop"
        assert hasattr(decision, 'reason'), "Нет reason"
        assert hasattr(decision, 'score'), "Нет score"
        assert 0 <= decision.score <= 10, f"Оценка вне диапазона: {decision.score}"
        
        # Если should_stop=True, должен быть improved_response
        if decision.should_stop:
            assert decision.improved_response, "Нет улучшенного ответа при остановке"
