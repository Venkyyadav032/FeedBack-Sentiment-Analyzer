import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.analytics import (
    OverviewKPISchema,
    SentimentDistributionSchema,
    SentimentTrendsSchema,
    CategorySentimentSchema
)
from app.services.report_service import (
    get_overview_kpis,
    get_sentiment_distribution,
    get_sentiment_trends,
    get_category_sentiment_breakdown
)
from app.services.issue_detection_service import get_formatted_issues

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview", response_model=OverviewKPISchema)
def get_analytics_overview(db: Session = Depends(get_db)):
    return get_overview_kpis(db)

@router.get("/sentiment", response_model=SentimentDistributionSchema)
def get_sentiment_summary(db: Session = Depends(get_db)):
    return get_sentiment_distribution(db)

@router.get("/trends", response_model=SentimentTrendsSchema)
def get_sentiment_trends_data(
    timeframe: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db)
):
    trends_list = get_sentiment_trends(db, days=days)
    return {
        "timeframe": timeframe,
        "trends": trends_list
    }

@router.get("/issues", response_model=List[Dict[str, Any]])
def get_improvement_issues(db: Session = Depends(get_db)):
    return get_formatted_issues(db)

@router.get("/category-sentiment", response_model=List[CategorySentimentSchema])
def get_category_sentiment(db: Session = Depends(get_db)):
    return get_category_sentiment_breakdown(db)
