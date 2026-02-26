"""
База знаний для Sokrat Research System.
Асинхронная версия с aiosqlite.
"""
import aiosqlite
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

class KnowledgeBase:
    """
    Асинхронная база знаний с SQLite хранилищем.
    """
    
    def __init__(self, db_path: str = "data/sokrat.db"):
        """
        Инициализация БД.
        
        Args:
            db_path: путь к файлу SQLite
        """
        self.db_path = db_path
        
        # Создаём директорию для БД если нужно
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    async def _init_db(self):
        """Создание всех необходимых таблиц (асинхронно)."""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица для исследовательских сессий
            await db.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                config JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active'
            )
            """)
            
            # Таблица для раундов
            await db.execute("""
            CREATE TABLE IF NOT EXISTS research_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
            )
            """)
            
            # Индекс для быстрого поиска по сессии
            await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rounds_session 
            ON research_rounds(session_id)
            """)
            
            # Таблица для экспертиз
            await db.execute("""
            CREATE TABLE IF NOT EXISTS expertise_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                expert_type TEXT NOT NULL,
                findings JSON NOT NULL,
                suggestions JSON NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id) ON DELETE CASCADE
            )
            """)
            
            # Индекс для быстрого поиска экспертиз
            await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_expertise_session 
            ON expertise_results(session_id)
            """)
            
            await db.commit()
    
    async def save_session(self, session_id: str, task: str, config: dict):
        """
        Сохранить сессию (асинхронно).
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO research_sessions (id, task, config, created_at, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    task,
                    json.dumps(config, ensure_ascii=False),
                    datetime.now().isoformat(),
                    'active'
                )
            )
            await db.commit()
    
    async def save_round(self, session_id: str, round_number: int, data: dict):
        """
        Сохранить раунд исследования (асинхронно).
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO research_rounds (session_id, round_number, data, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    round_number,
                    json.dumps(data, ensure_ascii=False),
                    datetime.now().isoformat()
                )
            )
            await db.commit()
    
    async def save_expertise(
        self,
        session_id: str,
        round_number: int,
        expert_type: str,
        findings: list,
        suggestions: list,
        score: float
    ):
        """
        Сохранить результат экспертизы (асинхронно).
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO expertise_results 
                (session_id, round_number, expert_type, findings, suggestions, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    round_number,
                    expert_type,
                    json.dumps(findings, ensure_ascii=False),
                    json.dumps(suggestions, ensure_ascii=False),
                    score,
                    datetime.now().isoformat()
                )
            )
            await db.commit()
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Получить полную историю сессии (асинхронно).
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем сессию
            cursor = await db.execute(
                "SELECT * FROM research_sessions WHERE id = ?",
                (session_id,)
            )
            session = await cursor.fetchone()
            
            # Получаем раунды
            cursor = await db.execute(
                "SELECT * FROM research_rounds WHERE session_id = ? ORDER BY round_number",
                (session_id,)
            )
            rounds = await cursor.fetchall()
            
            # Получаем экспертизы
            cursor = await db.execute(
                "SELECT * FROM expertise_results WHERE session_id = ? ORDER BY round_number",
                (session_id,)
            )
            expertise = await cursor.fetchall()
            
            return {
                "session": session,
                "rounds": rounds,
                "expertise": expertise
            }
    
    async def session_exists(self, session_id: str) -> bool:
        """Проверить существование сессии (асинхронно)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM research_sessions WHERE id = ?",
                (session_id,)
            )
            result = await cursor.fetchone()
            return result is not None
    
    async def delete_session(self, session_id: str):
        """Удалить сессию и все связанные данные (асинхронно)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM research_sessions WHERE id = ?",
                (session_id,)
            )
            await db.commit()
    
    async def get_all_sessions(self, limit: int = 100) -> List[Tuple]:
        """Получить список всех сессий (асинхронно)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, task, created_at, status 
                FROM research_sessions 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (limit,)
            )
            return await cursor.fetchall()
