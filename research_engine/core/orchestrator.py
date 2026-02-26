"""
Оркестратор Research Engine - управляет исследовательским процессом.
"""
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

from .models import (
    SessionContext, ExpertiseResult, ModelResponse,
    DiscussionRound, JudgeDecision
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchOrchestrator:
    """
    Оркестратор, управляющий исследовательским процессом.
    """
    
    def __init__(self, llm_client=None, kb_client=None):
        """
        Args:
            llm_client: Клиент для вызова моделей (из sokrat_core)
            kb_client: Клиент для базы знаний
        """
        self.llm = llm_client
        self.kb = kb_client
        self.experts = {
            'code': self._expert_code,
            'prompt': self._expert_prompt,
            'analytics': self._expert_analytics
        }
    
    async def run(self, context: SessionContext) -> SessionContext:
        """
        Запустить полный исследовательский цикл.
        
        Args:
            context: Контекст сессии с задачей
            
        Returns:
            SessionContext: Обновлённый контекст с результатами
        """
        logger.info(f" Запуск сессии {context.session_id}")
        logger.info(f"Задача: {context.task[:100]}...")
        
        # Сохраняем начало в БЗ
        if self.kb:
            await self._save_checkpoint(context, "session_started")
        
        try:
            # Шаг 1: Первичный ответ (TODO: заменить на реальный вызов)
            context.primary_response = await self._get_primary_response(context)
            await self._save_checkpoint(context, "primary_response")
            
            # Шаг 2: Экспертизы
            logger.info(" Запуск экспертиз...")
            expertise = await self._run_expertise_round(context.primary_response.content)
            context.expertise_results.extend(expertise)
            
            # Сохраняем экспертизы в БЗ
            if self.kb:
                for exp in expertise:
                    await self.kb.save_expertise(
                        context.session_id,
                        context.current_round,
                        exp.expert_type,
                        exp.findings,
                        exp.suggestions,
                        exp.score
                    )
            
            # Шаг 3: Обсуждение
            logger.info(" Круг обсуждения...")
            discussion = await self._run_discussion_round(context)
            context.discussion_rounds.append(discussion)
            
            # Шаг 4: Судья
            logger.info(" Судья оценивает...")
            judge = await self._run_judge(context)
            
            # Обновляем метрики
            context.quality_score = judge.score
            context.improvement_trend.append(judge.score)
            
            # Финальный синтез
            context.is_finished = True
            context.final_synthesis = judge.improved_response
            
            # Сохраняем результат
            await self._save_checkpoint(context, "completed")
            logger.info(f" Сессия {context.session_id} завершена, оценка: {context.quality_score}/10")
            
            return context
            
        except Exception as e:
            logger.error(f" Ошибка: {e}")
            await self._save_checkpoint(context, "failed", error=str(e))
            raise
    
    async def _get_primary_response(self, context: SessionContext) -> ModelResponse:
        """
        Получить первичный ответ от модели.
        TODO: Заменить на реальный вызов из sokrat_core
        """
        # Здесь будет вызов dispatch_to_models из sokrat_core
        return ModelResponse(
            model_name="gpt-4",
            content=f"[Тестовый ответ] Задача: {context.task}. Используем быструю сортировку с оптимизацией памяти.",
            tokens_used=150,
            latency_ms=1200
        )
    
    async def _run_expertise_round(self, content: str) -> List[ExpertiseResult]:
        """
        Запустить все контуры экспертизы параллельно.
        """
        tasks = [
            self.experts['code'](content),
            self.experts['prompt'](content),
            self.experts['analytics'](content)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем ошибки
        expertise_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка в экспертизе: {result}")
                expertise_results.append(
                    ExpertiseResult(
                        expert_type="error",
                        findings=[f"Ошибка: {result}"],
                        suggestions=["Повторить попытку"],
                        score=0
                    )
                )
            else:
                expertise_results.append(result)
        
        return expertise_results
    
    async def _expert_code(self, content: str) -> ExpertiseResult:
        """Эксперт по коду"""
        # TODO: Заменить на реальный вызов модели
        return ExpertiseResult(
            expert_type="code",
            findings=[
                "Используется рекурсия, может быть проблема с глубиной",
                "Нет обработки пустого массива",
                "Можно оптимизировать память"
            ],
            suggestions=[
                "Добавить итеративную реализацию",
                "Проверить граничные случаи",
                "Использовать in-place сортировку"
            ],
            score=7.5
        )
    
    async def _expert_prompt(self, content: str) -> ExpertiseResult:
        """Эксперт по промпт-инженерии"""
        return ExpertiseResult(
            expert_type="prompt",
            findings=[
                "Промпт не уточняет тип сортировки",
                "Не указаны требования к памяти"
            ],
            suggestions=[
                "Добавить: 'реализуй быструю сортировку с оптимизацией памяти'",
                "Уточнить: 'для больших массивов (до 1M элементов)'"
            ],
            score=8.0
        )
    
    async def _expert_analytics(self, content: str) -> ExpertiseResult:
        """Эксперт по аналитике"""
        return ExpertiseResult(
            expert_type="analytics",
            findings=[
                "Сложность O(n log n) не указана",
                "Нет сравнения с другими алгоритмами"
            ],
            suggestions=[
                "Добавить анализ сложности",
                "Сравнить с сортировкой слиянием"
            ],
            score=6.5
        )
    
    async def _run_discussion_round(self, context: SessionContext) -> DiscussionRound:
        """
        Запустить круг обсуждения между моделями.
        TODO: Заменить на реальные вызовы моделей
        """
        # Здесь будут реальные вызовы моделей
        return DiscussionRound(
            round_number=context.current_round + 1,
            responses={
                "gpt-4": "Предлагаю использовать in-place quick sort...",
                "claude": "Согласен, но добавим обработку дубликатов...",
                "deepseek": "Можно оптимизировать выбор опорного элемента..."
            },
            consensus_reached=False
        )
    
    async def _run_judge(self, context: SessionContext) -> JudgeDecision:
        """
        Судья оценивает прогресс.
        TODO: Заменить на реальный вызов модели-судьи
        """
        return JudgeDecision(
            should_stop=True,
            reason="Достигнуто хорошее качество, все эксперты довольны",
            improved_response="""
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
            """,
            score=8.5,
            needs_more_rounds=False
        )
    
    async def _save_checkpoint(self, context: SessionContext, stage: str, error: str = None):
        """Сохранить чекпоинт в базу знаний"""
        if not self.kb:
            return
        
        try:
            if stage == "session_started":
                await self.kb.save_session(
                    context.session_id,
                    context.task,
                    {
                        "initial_prompt": context.initial_prompt,
                        "rag_context": context.rag_context,
                        "negative_constraints": context.negative_constraints,
                        "max_rounds": context.max_rounds
                    }
                )
            elif stage == "primary_response" and context.primary_response:
                await self.kb.save_round(
                    context.session_id,
                    0,
                    {
                        "type": "primary",
                        "model": context.primary_response.model_name,
                        "content": context.primary_response.content,
                        "tokens": context.primary_response.tokens_used
                    }
                )
            elif stage == "completed":
                await self.kb.save_round(
                    context.session_id,
                    context.current_round,
                    {
                        "type": "final",
                        "synthesis": context.final_synthesis,
                        "quality_score": context.quality_score
                    }
                )
        except Exception as e:
            logger.error(f"Ошибка сохранения чекпоинта: {e}")
