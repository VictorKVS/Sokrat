from fastapi import FastAPI
from src.api.routes import router
from src.utils.logging_config import get_logger
import uvicorn

logger = get_logger(__name__)

app = FastAPI(
    title="Sokrat - Multi-LLM Analysis System",
    description="Модуль сбора и распределения информации",
    version="0.1.0"
)

app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Sokrat API",
        "status": "running",
        "version": "0.1.0",
        "endpoints": {
            "POST /analyze": "Анализ запроса",
            "GET /health": "Проверка здоровья"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
