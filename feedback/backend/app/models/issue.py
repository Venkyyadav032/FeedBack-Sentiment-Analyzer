from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

# Association table for Many-to-Many relationship between ImprovementIssue and Feedback
issue_feedback = Table(
    "issue_feedback",
    Base.metadata,
    Column("issue_id", Integer, ForeignKey("improvement_issues.id", ondelete="CASCADE"), primary_key=True),
    Column("feedback_id", Integer, ForeignKey("feedback.id", ondelete="CASCADE"), primary_key=True)
)

class ImprovementIssue(Base):
    __tablename__ = "improvement_issues"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    occurrence_count = Column(Integer, nullable=False, default=1)
    priority = Column(String(20), nullable=False, default="Medium", index=True) # High, Medium, Low
    suggested_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    feedbacks = relationship("Feedback", secondary=issue_feedback, back_populates="issues")
