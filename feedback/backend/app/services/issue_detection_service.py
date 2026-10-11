import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.feedback import Feedback
from app.models.analysis import SentimentAnalysis
from app.models.issue import ImprovementIssue, issue_feedback

logger = logging.getLogger(__name__)

# Predefined Issue Templates & Heuristic Groupings
ISSUE_RULES = [
    {
        "keywords": ["support", "agent", "email", "respond", "ticket", "response", "unresolved"],
        "title": "Slow & Unresponsive Customer Support Response",
        "category": "Customer Support",
        "priority_threshold": 3,
        "suggested_action": "Establish strict 24-hour SLA targets for customer tickets and expand support agent headcount during peak hours."
    },
    {
        "keywords": ["delivery", "late", "shipping", "package", "arrived", "damaged"],
        "title": "Shipping Delays and Package Handling Issues",
        "category": "Delivery and Shipping",
        "priority_threshold": 3,
        "suggested_action": "Partner with reliable logistics providers and implement real-time order tracking and customer notifications."
    },
    {
        "keywords": ["expensive", "pricing", "fee", "cost", "cheaper", "tier"],
        "title": "High Pricing & Lack of Flexible Entry Tier",
        "category": "Pricing",
        "priority_threshold": 2,
        "suggested_action": "Evaluate introduction of a lightweight starter pricing tier for small businesses and audit checkout fee transparency."
    },
    {
        "keywords": ["crash", "crashes", "bug", "bugs", "error", "stability", "hang"],
        "title": "Application Instability & Frequent Crashes",
        "category": "Performance",
        "priority_threshold": 2,
        "suggested_action": "Deploy urgent emergency patch updates to stabilize app runtime and improve exception handling during heavy load."
    },
    {
        "keywords": ["search", "checkout", "navigate", "slow", "usability"],
        "title": "Checkout Page Errors and Navigation Friction",
        "category": "Website Usability",
        "priority_threshold": 2,
        "suggested_action": "Redesign checkout validation workflow and optimize search index query performance."
    },
    {
        "keywords": ["export", "pdf", "feature", "enterprise", "locked"],
        "title": "Feature Requests for Advanced Export Capabilities",
        "category": "Feature Requests",
        "priority_threshold": 2,
        "suggested_action": "Prioritize direct PDF/CSV exporter features in the upcoming product roadmap sprint."
    }
]

def sync_improvement_issues(db: Session) -> List[ImprovementIssue]:
    """
    Analyzes negative and neutral feedback stored in DB to automatically detect, group,
    and update improvement issues.
    """
    try:
        # Fetch all negative/neutral feedbacks with their analyses
        feedbacks = db.query(Feedback).join(SentimentAnalysis).filter(
            SentimentAnalysis.sentiment.in_(["Negative", "Neutral"])
        ).all()
        
        total_feedback_count = db.query(func.count(Feedback.id)).scalar() or 1

        # Clear existing mappings dynamically
        db.execute(issue_feedback.delete())
        db.query(ImprovementIssue).delete()
        db.commit()

        created_issues = []

        for rule in ISSUE_RULES:
            matching_feedbacks = []
            for fb in feedbacks:
                text_lower = fb.feedback_text.lower()
                if any(kw in text_lower for kw in rule["keywords"]):
                    matching_feedbacks.append(fb)

            if matching_feedbacks:
                count = len(matching_feedbacks)
                priority = "High" if count >= rule["priority_threshold"] else "Medium" if count > 1 else "Low"
                mention_pct = round((count / total_feedback_count) * 100, 1)

                issue = ImprovementIssue(
                    title=rule["title"],
                    category=rule["category"],
                    description=f"Grouped issue matching keywords: {', '.join(rule['keywords'][:4])}. Mentioned in {count} feedback entries ({mention_pct}% of overall feedback).",
                    occurrence_count=count,
                    priority=priority,
                    suggested_action=rule["suggested_action"]
                )
                
                # Associate matched feedbacks
                issue.feedbacks.extend(matching_feedbacks)
                db.add(issue)
                created_issues.append(issue)

        db.commit()
        return created_issues
    except Exception as e:
        db.rollback()
        logger.error("Error synchronizing improvement issues: %s", str(e))
        return []

def get_formatted_issues(db: Session) -> List[Dict[str, Any]]:
    # Sync first to ensure fresh data
    sync_improvement_issues(db)
    
    total_feedback_count = db.query(func.count(Feedback.id)).scalar() or 1
    issues = db.query(ImprovementIssue).order_by(
        ImprovementIssue.occurrence_count.desc()
    ).all()

    formatted = []
    for issue in issues:
        mention_pct = round((issue.occurrence_count / total_feedback_count) * 100, 1)
        examples = [f.feedback_text for f in issue.feedbacks[:3]]
        
        formatted.append({
            "id": issue.id,
            "title": issue.title,
            "category": issue.category,
            "description": issue.description,
            "occurrence_count": issue.occurrence_count,
            "mention_percentage": mention_pct,
            "priority": issue.priority,
            "associated_sentiment": "Negative",
            "suggested_action": issue.suggested_action,
            "representative_examples": examples,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at
        })
    return formatted
