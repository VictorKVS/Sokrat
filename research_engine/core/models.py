"""
Модели данных для Research Engine.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class ExpertiseResult(BaseModel):
    """Результат работы контура экспертизы"""
    expert_type: str  # 'code', 'prompt', 'analytics'
    findings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float = Field(ge=0, le=10, default=5.0)
    raw_response: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

class ModelResponse(BaseModel):
    """Ответ от конкретной модели"""
    model_name: str
    content: str
    tokens_used: int = 0
    latency_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)

class DiscussionRound(BaseModel):
    """Результаты раунда обсуждения"""
    round_number: int
    responses: Dict[str, str] = Field(default_factory=dict)
    consensus_reached: bool = False
    best_response: Optional[str] = None

class SessionContext(BaseModel):
    """Полный контекст исследовательской сессии"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str
    initial_prompt: str
    rag_context: Optional[str] = None
    negative_constraints: Optional[str] = None
    
    # Состояние
    primary_response: Optional[ModelResponse] = None
    expertise_results: List[ExpertiseResult] = Field(default_factory=list)
    discussion_rounds: List[DiscussionRound] = Field(default_factory=list)
    
    # Управление
    current_round: int = 0
    max_rounds: int = 3
    is_finished: bool = False
    final_synthesis: Optional[str] = None
    
    # Метрики
    quality_score: float = 0.0
    improvement_trend: List[float] = Field(default_factory=list)

class JudgeDecision(BaseModel):
    """Решение судьи"""
    should_stop: bool
    reason: str
    improved_response: str
    score: float
    needs_more_rounds: bool
