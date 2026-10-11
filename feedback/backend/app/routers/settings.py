import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.connection import get_db, DB_TYPE
from app.models.feedback import Feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("")
def get_system_settings(db: Session = Depends(get_db)):
    feedback_count = db.query(Feedback).count()
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database_type": DB_TYPE.upper(),
        "mysql_database": settings.MYSQL_DB if DB_TYPE == "mysql" else "SQLite (Fallback)",
        "model_version": "v1.0.0-tfidf-hybrid",
        "supported_languages": ["English (US/UK)"],
        "auto_analyze_enabled": True,
        "confidence_threshold": 0.60,
        "total_feedbacks_indexed": feedback_count,
        "cors_origins": settings.cors_origins_list
    }
