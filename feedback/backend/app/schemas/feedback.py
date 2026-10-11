from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class AnalysisResultSchema(BaseModel):
    sentiment: str
    confidence_score: float
    keywords: List[str]
    detected_topic: Optional[str] = None
    explanation: Optional[str] = None
    suggested_action: Optional[str] = None
    model_version: str = "v1.0.0-tfidf-hybrid"

    class Config:
        from_attributes = True

class FeedbackCreateSchema(BaseModel):
    feedback_text: str = Field(..., min_length=2, description="The customer feedback or review text")
    product_or_service: Optional[str] = "General"
    category: Optional[str] = "User Experience"
    rating: Optional[int] = Field(None, ge=1, le=5)
    source: Optional[str] = "Manual"
    user_id: Optional[int] = None
    submitted_at: Optional[datetime] = None

class FeedbackUpdateSchema(BaseModel):
    feedback_text: Optional[str] = None
    product_or_service: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    source: Optional[str] = None

class FeedbackResponseSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    feedback_text: str
    source: str
    product_or_service: str
    category: str
    rating: Optional[int] = None
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime
    analysis: Optional[AnalysisResultSchema] = None

    class Config:
        from_attributes = True

class BatchAnalyzeRequest(BaseModel):
    texts: List[str]
    product_or_service: Optional[str] = "General"
    category: Optional[str] = "General"
    save_to_db: bool = False

class BulkDeleteRequest(BaseModel):
    ids: List[int]
