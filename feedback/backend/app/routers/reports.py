import io
import csv
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.feedback import Feedback
from app.models.analysis import SentimentAnalysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/export")
def export_feedback_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Feedback).join(SentimentAnalysis)
    
    if sentiment:
        query = query.filter(SentimentAnalysis.sentiment == sentiment)
    if category and category != "All":
        query = query.filter(Feedback.category == category)
        
    records = query.order_by(Feedback.submitted_at.desc()).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        writer.writerow([
            "ID", "Submitted Date", "Feedback Text", "Product/Service",
            "Category", "Source", "Rating", "Sentiment", "Confidence", "Detected Topic"
        ])
        
        for fb in records:
            sent = fb.analysis.sentiment if fb.analysis else "N/A"
            conf = fb.analysis.confidence_score if fb.analysis else 0.0
            topic = fb.analysis.detected_topic if fb.analysis else "N/A"
            
            writer.writerow([
                fb.id,
                fb.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if fb.submitted_at else "",
                fb.feedback_text,
                fb.product_or_service,
                fb.category,
                fb.source,
                fb.rating if fb.rating else "",
                sent,
                conf,
                topic
            ])
            
        csv_data = output.getvalue()
        filename = f"feedbacksense_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        # JSON export
        json_data = []
        for fb in records:
            json_data.append({
                "id": fb.id,
                "submitted_at": fb.submitted_at.isoformat() if fb.submitted_at else None,
                "feedback_text": fb.feedback_text,
                "product_or_service": fb.product_or_service,
                "category": fb.category,
                "source": fb.source,
                "rating": fb.rating,
                "sentiment": fb.analysis.sentiment if fb.analysis else None,
                "confidence_score": fb.analysis.confidence_score if fb.analysis else None,
                "detected_topic": fb.analysis.detected_topic if fb.analysis else None
            })
        return json_data
