from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id", ondelete="CASCADE"), nullable=False, unique=True)
    sentiment = Column(String(20), nullable=False, index=True) # Positive, Negative, Neutral
    confidence_score = Column(Float, nullable=False, default=0.0)
    keywords = Column(Text, nullable=True) # Stored as JSON string or comma-separated
    detected_topic = Column(String(150), nullable=True)
    explanation = Column(Text, nullable=True)
    model_version = Column(String(50), nullable=False, default="v1.0.0-tfidf-hybrid")
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    feedback = relationship("Feedback", back_populates="analysis")
