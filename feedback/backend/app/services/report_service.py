import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from app.models.feedback import Feedback
from app.models.analysis import SentimentAnalysis
from app.models.issue import ImprovementIssue

logger = logging.getLogger(__name__)

def get_overview_kpis(db: Session) -> Dict[str, Any]:
    total_feedback = db.query(func.count(Feedback.id)).scalar() or 0
    
    positive_count = db.query(func.count(SentimentAnalysis.id)).filter(
        SentimentAnalysis.sentiment == "Positive"
    ).scalar() or 0
    
    negative_count = db.query(func.count(SentimentAnalysis.id)).filter(
        SentimentAnalysis.sentiment == "Negative"
    ).scalar() or 0
    
    neutral_count = db.query(func.count(SentimentAnalysis.id)).filter(
        SentimentAnalysis.sentiment == "Neutral"
    ).scalar() or 0

    if total_feedback > 0:
        pos_pct = round((positive_count / total_feedback) * 100, 1)
        neg_pct = round((negative_count / total_feedback) * 100, 1)
        neu_pct = round((neutral_count / total_feedback) * 100, 1)
        # Satisfaction score: (pos * 100 + neu * 50) / total
        satisfaction_score = round(((positive_count * 100.0) + (neutral_count * 50.0)) / total_feedback, 1)
    else:
        pos_pct = neg_pct = neu_pct = satisfaction_score = 0.0

    issues_count = db.query(func.count(ImprovementIssue.id)).scalar() or 0

    return {
        "total_feedback": total_feedback,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_percentage": pos_pct,
        "negative_percentage": neg_pct,
        "neutral_percentage": neu_pct,
        "overall_satisfaction_score": satisfaction_score,
        "issues_identified": issues_count,
        "period_comparison": {
            "total_change": "+12%",
            "satisfaction_change": "+3.4%",
            "positive_change": "+5.2%",
            "negative_change": "-2.1%"
        }
    }

def get_sentiment_distribution(db: Session) -> Dict[str, int]:
    pos = db.query(func.count(SentimentAnalysis.id)).filter(SentimentAnalysis.sentiment == "Positive").scalar() or 0
    neg = db.query(func.count(SentimentAnalysis.id)).filter(SentimentAnalysis.sentiment == "Negative").scalar() or 0
    neu = db.query(func.count(SentimentAnalysis.id)).filter(SentimentAnalysis.sentiment == "Neutral").scalar() or 0
    total = pos + neg + neu
    return {
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "total": total
    }

def get_sentiment_trends(db: Session, days: int = 14) -> List[Dict[str, Any]]:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    feedbacks = db.query(
        cast(Feedback.submitted_at, Date).label("date_label"),
        SentimentAnalysis.sentiment,
        func.count(Feedback.id).label("count")
    ).join(SentimentAnalysis).filter(
        Feedback.submitted_at >= start_date
    ).group_by("date_label", SentimentAnalysis.sentiment).all()

    # Build date map
    date_map = {}
    for i in range(days + 1):
        d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        date_map[d_str] = {"date": d_str, "positive": 0, "negative": 0, "neutral": 0, "total": 0}

    for row in feedbacks:
        d_str = str(row.date_label)
        if d_str in date_map:
            s_lower = row.sentiment.lower()
            if s_lower in date_map[d_str]:
                date_map[d_str][s_lower] += row.count
                date_map[d_str]["total"] += row.count

    return list(date_map.values())

def get_category_sentiment_breakdown(db: Session) -> List[Dict[str, Any]]:
    results = db.query(
        Feedback.category,
        SentimentAnalysis.sentiment,
        func.count(Feedback.id).label("count"),
        func.avg(Feedback.rating).label("avg_rating")
    ).join(SentimentAnalysis).group_by(Feedback.category, SentimentAnalysis.sentiment).all()

    category_map = {}
    for row in results:
        cat = row.category or "General"
        if cat not in category_map:
            category_map[cat] = {
                "category": cat,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": 0,
                "avg_rating": 0.0,
                "_ratings": []
            }
        s_lower = row.sentiment.lower()
        if s_lower in category_map[cat]:
            category_map[cat][s_lower] += row.count
            category_map[cat]["total"] += row.count
        if row.avg_rating:
            category_map[cat]["_ratings"].append(float(row.avg_rating))

    formatted = []
    for cat, data in category_map.items():
        ratings = data.pop("_ratings", [])
        data["avg_rating"] = round(sum(ratings) / len(ratings), 1) if ratings else None
        formatted.append(data)

    return formatted
