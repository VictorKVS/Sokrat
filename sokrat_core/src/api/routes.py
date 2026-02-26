from fastapi import APIRouter, HTTPException
from src.api.models import AnalysisRequest, AnalysisResponse
from src.core.orchestrator import AnalysisOrchestrator
from src.utils.logging_config import get_logger

router = APIRouter()
orchestrator = AnalysisOrchestrator()
logger = get_logger(__name__)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Анализ запроса с веб-поиском и мульти-модельным разбором"""
    try:
        logger.info(f" Получен запрос: {request.query}")
        result = await orchestrator.run_analysis(request.query)
        logger.info(" Анализ завершён")
        return result
    except Exception as e:
        logger.error(f" Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "healthy"}
