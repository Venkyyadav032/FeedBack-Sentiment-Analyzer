from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class OverviewKPISchema(BaseModel):
    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    overall_satisfaction_score: float  # 0 to 100 or 1 to 5 scale
    issues_identified: int
    period_comparison: Dict[str, Any]

class SentimentDistributionSchema(BaseModel):
    positive: int
    negative: int
    neutral: int
    total: int

class SentimentTrendPoint(BaseModel):
    date: str
    positive: int
    negative: int
    neutral: int
    total: int

class SentimentTrendsSchema(BaseModel):
    timeframe: str # daily, weekly, monthly
    trends: List[SentimentTrendPoint]

class ImprovementIssueSchema(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str] = None
    occurrence_count: int
    mention_percentage: float
    priority: str # High, Medium, Low
    associated_sentiment: str = "Negative"
    suggested_action: Optional[str] = None
    representative_examples: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CategorySentimentSchema(BaseModel):
    category: str
    positive: int
    negative: int
    neutral: int
    total: int
    avg_rating: Optional[float] = None
