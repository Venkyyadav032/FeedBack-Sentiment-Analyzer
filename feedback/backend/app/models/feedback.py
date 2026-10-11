from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feedback_text = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, default="Manual", index=True)
    product_or_service = Column(String(150), nullable=False, default="General")
    category = Column(String(100), nullable=False, default="User Experience", index=True)
    rating = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="feedbacks")
    analysis = relationship("SentimentAnalysis", back_populates="feedback", uselist=False, cascade="all, delete-orphan")
    issues = relationship("ImprovementIssue", secondary="issue_feedback", back_populates="feedbacks")
