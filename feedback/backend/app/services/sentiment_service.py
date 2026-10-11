import re
import logging
from typing import Dict, Any, List
import numpy as np
from app.utils.text_processing import clean_text, extract_keywords

logger = logging.getLogger(__name__)

# Try importing scikit-learn
HAS_SKLEARN = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("Scikit-learn not available. Sentiment Engine using Lexicon Rule Classifier.")

# Baseline sentiment lexicons for rule-assisted feature weighting & fallback
POSITIVE_LEXICON = {
    "love", "excellent", "great", "awesome", "fantastic", "good", "helpful", "fast",
    "perfect", "perfectly", "amazing", "durable", "premium", "best", "satisfied", "impressive",
    "outstanding", "superb", "recommending", "smooth", "resolved", "decent", "exceeds",
    "prompt", "easy", "thank", "thanks", "valuable", "happy", "liked", "like", "wonderful"
}

NEGATIVE_LEXICON = {
    "bad", "terrible", "horrible", "awful", "late", "slow", "expensive", "crash",
    "crashes", "crashed", "bug", "bugs", "error", "errors", "issue", "issues",
    "broken", "poor", "unresolved", "disappointing", "disappointed", "refund", "locked",
    "waste", "hard", "difficult", "fail", "failed", "failure", "worst", "hidden",
    "unresponsive", "damaged", "overpriced", "useless", "hate", "stuck", "frustrating"
}

# Training dataset for the ML Classifier
TRAINING_TEXTS = [
    ("The product works perfectly and the support team was super helpful when I had setup questions.", "Positive"),
    ("My delivery arrived late and customer support did not respond to my emails for three days.", "Negative"),
    ("The product was delivered yesterday and includes the standard accessories as advertised.", "Neutral"),
    ("Absolutely love the new user interface! It is smooth, fast, and easy to navigate.", "Positive"),
    ("The subscription pricing is too expensive for small businesses. Needs a cheaper entry tier.", "Negative"),
    ("Frequent crashes after the latest software update. Needs urgent bug fixes for stability.", "Negative"),
    ("Customer service agent Sarah resolved my refund request within five minutes. Excellent service!", "Positive"),
    ("Packaging was damaged upon arrival, but the item inside remained intact and functioning.", "Neutral"),
    ("The website search feature is very slow and often returns irrelevant search results.", "Negative"),
    ("Outstanding build quality! Feels premium and durable. Worth every penny.", "Positive"),
    ("The checkout page keeps throwing error codes when processing credit card payments.", "Negative"),
    ("Standard account features are decent, but export functionality is locked behind enterprise plans.", "Neutral"),
    ("System uptime is impressive. We experienced 99.9% availability throughout the entire month.", "Positive"),
    ("Hidden fees were added at checkout without clear explanation. Very disappointing pricing policy.", "Negative"),
    ("Received standard confirmation email after submitting request. Waiting for further update.", "Neutral"),
    ("The battery life exceeds expectations. Easily lasts two full days on a single charge.", "Positive"),
    ("The analytics reports are difficult to export to PDF format. Please add one-click export.", "Negative"),
    ("Prompt response from support agent, but the technical issue is still unresolved after 48 hours.", "Negative")
]

class SentimentEngine:
    def __init__(self):
        self.is_trained = False
        if HAS_SKLEARN:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
            self.classifier = LogisticRegression(C=1.0, max_iter=200)
            self._train_model()

    def _train_model(self):
        if not HAS_SKLEARN:
            return
        try:
            texts, labels = zip(*TRAINING_TEXTS)
            cleaned_texts = [clean_text(t) for t in texts]
            X = self.vectorizer.fit_transform(cleaned_texts)
            self.classifier.fit(X, labels)
            self.is_trained = True
            logger.info("SentimentEngine ML model trained successfully with %d samples.", len(texts))
        except Exception as e:
            logger.error("Failed to train sentiment ML model: %s", str(e))
            self.is_trained = False

    def predict(self, text: str, rating: int = None) -> Dict[str, Any]:
        cleaned = clean_text(text)
        if not cleaned:
            return {
                "sentiment": "Neutral",
                "confidence_score": 0.5,
                "keywords": [],
                "detected_topic": "General",
                "explanation": "Empty text provided.",
                "model_version": "v1.0.0-hybrid"
            }

        keywords = extract_keywords(cleaned, top_n=5)
        
        # 1. ML Classifier Prediction
        ml_sentiment = "Neutral"
        ml_confidence = 0.5
        
        if HAS_SKLEARN and self.is_trained:
            try:
                vec = self.vectorizer.transform([cleaned])
                probs = self.classifier.predict_proba(vec)[0]
                classes = self.classifier.classes_
                max_idx = np.argmax(probs)
                ml_sentiment = classes[max_idx]
                ml_confidence = float(probs[max_idx])
            except Exception as e:
                logger.warning("ML prediction failed, using fallback: %s", str(e))

        # 2. Lexicon Rule Scoring
        words = set(re.findall(r'\b\w+\b', cleaned))
        pos_hits = words.intersection(POSITIVE_LEXICON)
        neg_hits = words.intersection(NEGATIVE_LEXICON)
        
        pos_score = len(pos_hits)
        neg_score = len(neg_hits)
        
        if pos_score > neg_score:
            rule_sentiment = "Positive"
            rule_confidence = min(0.95, 0.65 + (pos_score * 0.1))
        elif neg_score > pos_score:
            rule_sentiment = "Negative"
            rule_confidence = min(0.95, 0.65 + (neg_score * 0.1))
        else:
            rule_sentiment = "Neutral"
            rule_confidence = 0.70

        # Dynamic selection
        if HAS_SKLEARN and self.is_trained and ml_confidence >= 0.55:
            final_sentiment = ml_sentiment
            final_confidence = round(float(ml_confidence), 2)
            model_ver = "v1.0.0-tfidf-logistic"
        else:
            final_sentiment = rule_sentiment
            final_confidence = round(float(rule_confidence), 2)
            model_ver = "v1.0.0-lexicon-rule"

        # Explanation
        found_key_words = list(pos_hits.union(neg_hits))
        if final_sentiment == "Positive":
            explanation = f"Detected positive sentiments supported by key terms like: {', '.join(found_key_words if found_key_words else keywords[:2])}."
        elif final_sentiment == "Negative":
            explanation = f"Identified negative sentiment expressing dissatisfaction regarding terms like: {', '.join(found_key_words if found_key_words else keywords[:2])}."
        else:
            explanation = "Feedback presents informative or neutral sentiment without strong emotional indicators."

        topic = self._detect_topic(cleaned)

        return {
            "sentiment": final_sentiment,
            "confidence_score": final_confidence,
            "keywords": keywords,
            "detected_topic": topic,
            "explanation": explanation,
            "model_version": model_ver
        }

    def _detect_topic(self, cleaned_text: str) -> str:
        if any(w in cleaned_text for w in ["support", "service", "agent", "ticket", "chat", "email", "help", "response"]):
            return "Customer Support"
        elif any(w in cleaned_text for w in ["delivery", "shipment", "shipping", "package", "arrived", "packaging"]):
            return "Delivery & Shipping"
        elif any(w in cleaned_text for w in ["price", "cost", "pricing", "expensive", "subscription", "fee", "fees"]):
            return "Pricing & Billing"
        elif any(w in cleaned_text for w in ["crash", "bug", "error", "slow", "performance", "hang", "uptime"]):
            return "Performance & Reliability"
        elif any(w in cleaned_text for w in ["ui", "interface", "ux", "search", "navigate", "checkout", "design"]):
            return "Website & App Usability"
        elif any(w in cleaned_text for w in ["feature", "export", "option", "button"]):
            return "Feature Requests"
        else:
            return "Product Quality"

sentiment_engine = SentimentEngine()

def analyze_single_feedback(text: str, rating: int = None) -> Dict[str, Any]:
    return sentiment_engine.predict(text, rating)
