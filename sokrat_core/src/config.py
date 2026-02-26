from pydantic_settings import BaseSettings
from typing import List
import json

class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/sokrat.db"
    
    # Search settings
    max_search_results: int = 8
    search_timeout: int = 10
    exclude_domains: List[str] = [
        "forum", "reddit.com", "quora.com", 
        "youtube.com", "facebook.com", "twitter.com"
    ]
    
    # Parser settings
    max_page_size_chars: int = 20000
    request_timeout: int = 15
    user_agent: str = "Mozilla/5.0 (compatible; SokratBot/1.0)"
    
    # Models
    models: List[str] = ["openai/gpt-4", "deepseek/deepseek-chat", "qwen/qwen-2.5-72b-instruct"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/sokrat.log"
    
    class Config:
        env_file = ".env"

settings = Settings()
