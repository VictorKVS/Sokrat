from pydantic import BaseModel
from typing import List, Dict, Optional

class AnalysisRequest(BaseModel):
    query: str

class SourceInfo(BaseModel):
    url: str
    title: str

class AnalysisResponse(BaseModel):
    query_id: str
    sources: List[SourceInfo]
    model_analyses: Dict[str, str]
    confidence_flags: List[str]
