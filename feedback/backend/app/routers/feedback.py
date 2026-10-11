import io
import json
import logging
from typing import Optional, List
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database.connection import get_db
from app.models.feedback import Feedback
from app.models.analysis import SentimentAnalysis
from app.schemas.feedback import (
    FeedbackCreateSchema,
    FeedbackUpdateSchema,
    FeedbackResponseSchema,
    AnalysisResultSchema,
    BatchAnalyzeRequest,
    BulkDeleteRequest
)
from app.services.sentiment_service import analyze_single_feedback
from app.services.issue_detection_service import sync_improvement_issues

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

@router.post("", response_model=FeedbackResponseSchema, status_code=status.HTTP_201_CREATED)
def create_and_analyze_feedback(
    payload: FeedbackCreateSchema,
    db: Session = Depends(get_db)
):
    try:
        # Create Feedback ORM instance
        new_fb = Feedback(
            user_id=payload.user_id,
            feedback_text=payload.feedback_text,
            source=payload.source or "Manual",
            product_or_service=payload.product_or_service or "General",
            category=payload.category or "User Experience",
            rating=payload.rating,
            submitted_at=payload.submitted_at or datetime.utcnow()
        )
        db.add(new_fb)
        db.flush() # obtain id

        # Run Sentiment Analysis Engine
        analysis_res = analyze_single_feedback(new_fb.feedback_text, rating=new_fb.rating)

        # Create SentimentAnalysis ORM record
        analysis_record = SentimentAnalysis(
            feedback_id=new_fb.id,
            sentiment=analysis_res["sentiment"],
            confidence_score=analysis_res["confidence_score"],
            keywords=json.dumps(analysis_res["keywords"]),
            detected_topic=analysis_res["detected_topic"],
            explanation=analysis_res["explanation"],
            model_version=analysis_res["model_version"]
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(new_fb)

        # Trigger issue sync in background
        sync_improvement_issues(db)

        # Parse keywords string to list for response schema
        if new_fb.analysis and isinstance(new_fb.analysis.keywords, str):
            new_fb.analysis.keywords = json.loads(new_fb.analysis.keywords)

        return new_fb
    except Exception as e:
        db.rollback()
        logger.error("Error creating feedback: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process feedback: {str(e)}")

@router.post("/analyze", response_model=List[AnalysisResultSchema])
def analyze_feedback_batch(
    request: BatchAnalyzeRequest,
    db: Session = Depends(get_db)
):
    if not request.texts:
        raise HTTPException(status_code=400, detail="Text list cannot be empty.")
    
    results = []
    for text in request.texts:
        analysis = analyze_single_feedback(text)
        results.append(AnalysisResultSchema(
            sentiment=analysis["sentiment"],
            confidence_score=analysis["confidence_score"],
            keywords=analysis["keywords"],
            detected_topic=analysis["detected_topic"],
            explanation=analysis["explanation"],
            suggested_action="Review feedback pattern and monitor user complaints." if analysis["sentiment"] == "Negative" else "Keep up good service quality.",
            model_version=analysis["model_version"]
        ))
        
        if request.save_to_db:
            fb = Feedback(
                feedback_text=text,
                product_or_service=request.product_or_service,
                category=request.category,
                source="Bulk API"
            )
            db.add(fb)
            db.flush()
            sa = SentimentAnalysis(
                feedback_id=fb.id,
                sentiment=analysis["sentiment"],
                confidence_score=analysis["confidence_score"],
                keywords=json.dumps(analysis["keywords"]),
                detected_topic=analysis["detected_topic"],
                explanation=analysis["explanation"]
            )
            db.add(sa)
    
    if request.save_to_db:
        db.commit()
        sync_improvement_issues(db)
        
    return results

@router.post("/upload")
def upload_bulk_feedback(
    file: UploadFile = File(...),
    text_column: str = Form("feedback_text"),
    product_column: Optional[str] = Form(None),
    category_column: Optional[str] = Form(None),
    rating_column: Optional[str] = Form(None),
    source_column: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or Excel (.xlsx/.xls) file.")

    contents = file.file.read()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Check text column presence
    target_col = text_column if text_column in df.columns else None
    if not target_col:
        # Fallback search for common column names
        for col in df.columns:
            if any(term in str(col).lower() for term in ["feedback", "review", "comment", "text"]):
                target_col = col
                break
    if not target_col:
        target_col = df.columns[0] # use first column if not found

    imported_count = 0
    errors = 0

    for _, row in df.iterrows():
        raw_text = str(row[target_col]).strip() if pd.notna(row[target_col]) else ""
        if not raw_text or raw_text.lower() == "nan":
            continue

        prod = str(row[product_column]).strip() if product_column and product_column in df.columns and pd.notna(row[product_column]) else "General"
        cat = str(row[category_column]).strip() if category_column and category_column in df.columns and pd.notna(row[category_column]) else "User Experience"
        src = str(row[source_column]).strip() if source_column and source_column in df.columns and pd.notna(row[source_column]) else "Bulk Upload"
        
        rating_val = None
        if rating_column and rating_column in df.columns and pd.notna(row[rating_column]):
            try:
                rating_val = int(row[rating_column])
            except:
                pass

        fb = Feedback(
            feedback_text=raw_text,
            product_or_service=prod,
            category=cat,
            rating=rating_val,
            source=src
        )
        db.add(fb)
        db.flush()

        analysis_res = analyze_single_feedback(raw_text, rating=rating_val)
        sa = SentimentAnalysis(
            feedback_id=fb.id,
            sentiment=analysis_res["sentiment"],
            confidence_score=analysis_res["confidence_score"],
            keywords=json.dumps(analysis_res["keywords"]),
            detected_topic=analysis_res["detected_topic"],
            explanation=analysis_res["explanation"],
            model_version=analysis_res["model_version"]
        )
        db.add(sa)
        imported_count += 1

    db.commit()
    sync_improvement_issues(db)

    return {
        "status": "success",
        "imported_count": imported_count,
        "message": f"Successfully uploaded and analyzed {imported_count} feedback entries."
    }

@router.get("/sample-csv")
def download_sample_csv():
    sample_content = (
        'feedback_text,product_or_service,category,rating,source\n'
        '"The app loading speed is amazing and easy to use.",Mobile App,User Experience,5,In-App\n'
        '"Customer service was rude and did not solve my issue.",Cloud Service,Customer Support,1,Email\n'
        '"Delivery arrived yesterday in standard condition.",E-Commerce,Delivery and Shipping,3,Website\n'
    )
    return Response(
        content=sample_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_feedback_template.csv"}
    )

@router.get("", response_model=dict)
def list_feedback(
    search: Optional[str] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    rating: Optional[int] = None,
    sort_by: str = Query("submitted_at", pattern="^(submitted_at|rating|id)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Feedback).join(SentimentAnalysis)

    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Feedback.feedback_text.like(search_fmt),
                Feedback.product_or_service.like(search_fmt),
                Feedback.category.like(search_fmt),
                SentimentAnalysis.sentiment.like(search_fmt)
            )
        )

    if sentiment:
        query = query.filter(SentimentAnalysis.sentiment == sentiment)

    if category and category != "All":
        query = query.filter(Feedback.category == category)

    if source and source != "All":
        query = query.filter(Feedback.source == source)

    if rating:
        query = query.filter(Feedback.rating == rating)

    total_records = query.count()

    # Sorting
    sort_col = getattr(Feedback, sort_by, Feedback.submitted_at)
    if order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    # Pagination
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    # Process keyword JSON for each item
    result_items = []
    for fb in items:
        item_dict = {
            "id": fb.id,
            "user_id": fb.user_id,
            "feedback_text": fb.feedback_text,
            "source": fb.source,
            "product_or_service": fb.product_or_service,
            "category": fb.category,
            "rating": fb.rating,
            "submitted_at": fb.submitted_at,
            "created_at": fb.created_at,
            "updated_at": fb.updated_at,
            "analysis": None
        }
        if fb.analysis:
            kw_list = []
            if fb.analysis.keywords:
                try:
                    kw_list = json.loads(fb.analysis.keywords)
                except:
                    kw_list = fb.analysis.keywords.split(",")
            item_dict["analysis"] = {
                "sentiment": fb.analysis.sentiment,
                "confidence_score": fb.analysis.confidence_score,
                "keywords": kw_list,
                "detected_topic": fb.analysis.detected_topic,
                "explanation": fb.analysis.explanation,
                "model_version": fb.analysis.model_version
            }
        result_items.append(item_dict)

    total_pages = (total_records + limit - 1) // limit if limit > 0 else 1

    return {
        "items": result_items,
        "total": total_records,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.get("/{feedback_id}", response_model=dict)
def get_feedback_detail(feedback_id: int, db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found.")

    kw_list = []
    if fb.analysis and fb.analysis.keywords:
        try:
            kw_list = json.loads(fb.analysis.keywords)
        except:
            kw_list = fb.analysis.keywords.split(",")

    return {
        "id": fb.id,
        "user_id": fb.user_id,
        "feedback_text": fb.feedback_text,
        "source": fb.source,
        "product_or_service": fb.product_or_service,
        "category": fb.category,
        "rating": fb.rating,
        "submitted_at": fb.submitted_at,
        "created_at": fb.created_at,
        "updated_at": fb.updated_at,
        "analysis": {
            "sentiment": fb.analysis.sentiment if fb.analysis else "Neutral",
            "confidence_score": fb.analysis.confidence_score if fb.analysis else 0.5,
            "keywords": kw_list,
            "detected_topic": fb.analysis.detected_topic if fb.analysis else "General",
            "explanation": fb.analysis.explanation if fb.analysis else "",
            "model_version": fb.analysis.model_version if fb.analysis else "v1.0.0"
        }
    }

@router.put("/{feedback_id}", response_model=dict)
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdateSchema,
    db: Session = Depends(get_db)
):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found.")

    text_changed = False
    if payload.feedback_text is not None and payload.feedback_text != fb.feedback_text:
        fb.feedback_text = payload.feedback_text
        text_changed = True

    if payload.product_or_service is not None:
        fb.product_or_service = payload.product_or_service
    if payload.category is not None:
        fb.category = payload.category
    if payload.source is not None:
        fb.source = payload.source
    if payload.rating is not None:
        fb.rating = payload.rating

    fb.updated_at = datetime.utcnow()

    # Re-analyze if text or rating changed
    if text_changed or payload.rating is not None:
        res = analyze_single_feedback(fb.feedback_text, rating=fb.rating)
        if fb.analysis:
            fb.analysis.sentiment = res["sentiment"]
            fb.analysis.confidence_score = res["confidence_score"]
            fb.analysis.keywords = json.dumps(res["keywords"])
            fb.analysis.detected_topic = res["detected_topic"]
            fb.analysis.explanation = res["explanation"]
            fb.analysis.analyzed_at = datetime.utcnow()
        else:
            sa = SentimentAnalysis(
                feedback_id=fb.id,
                sentiment=res["sentiment"],
                confidence_score=res["confidence_score"],
                keywords=json.dumps(res["keywords"]),
                detected_topic=res["detected_topic"],
                explanation=res["explanation"]
            )
            db.add(sa)

    db.commit()
    sync_improvement_issues(db)
    return {"status": "success", "message": "Feedback updated and re-analyzed."}

@router.delete("/{feedback_id}")
def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found.")

    db.delete(fb)
    db.commit()
    sync_improvement_issues(db)
    return {"status": "success", "message": f"Feedback #{feedback_id} deleted successfully."}

@router.post("/bulk-delete")
def bulk_delete_feedback(payload: BulkDeleteRequest, db: Session = Depends(get_db)):
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No IDs provided for bulk deletion.")

    deleted = db.query(Feedback).filter(Feedback.id.in_(payload.ids)).delete(synchronize_session=False)
    db.commit()
    sync_improvement_issues(db)
    return {"status": "success", "deleted_count": deleted, "message": f"Successfully deleted {deleted} items."}

@router.post("/seed")
def seed_sample_data(db: Session = Depends(get_db)):
    existing_count = db.query(Feedback).count()
    if existing_count > 0:
        return {"status": "info", "message": f"Database already contains {existing_count} records.", "seeded_count": 0}

    sample_items = [
        ("The product works perfectly and the support team was super helpful when I had setup questions.", "Mobile App", "Customer Support", 5, "App Store"),
        ("My delivery arrived late and customer support did not respond to my emails for three days.", "E-Commerce Platform", "Delivery and Shipping", 1, "Website Review"),
        ("The product was delivered yesterday and includes the standard accessories as advertised.", "Electronics", "Delivery and Shipping", 3, "Amazon Review"),
        ("Absolutely love the new user interface! It is smooth, fast, and easy to navigate.", "SaaS Dashboard", "User Experience", 5, "In-App Survey"),
        ("The subscription pricing is too expensive for small businesses. Needs a cheaper entry tier.", "Cloud Service", "Pricing", 2, "Email Survey"),
        ("Frequent crashes after the latest software update. Needs urgent bug fixes for stability.", "Mobile App", "Performance", 1, "Google Play"),
        ("Customer service agent Sarah resolved my refund request within five minutes. Excellent service!", "E-Commerce Platform", "Customer Support", 5, "Live Chat"),
        ("Packaging was damaged upon arrival, but the item inside remained intact and functioning.", "Home Decor", "Delivery and Shipping", 3, "Website Review"),
        ("The website search feature is very slow and often returns irrelevant search results.", "E-Commerce Platform", "Website Usability", 2, "In-App Survey"),
        ("Outstanding build quality! Feels premium and durable. Worth every penny.", "Electronics", "Product Quality", 5, "Trustpilot"),
        ("The checkout page keeps throwing error codes when processing credit card payments.", "E-Commerce Platform", "Website Usability", 1, "Helpdesk Ticket"),
        ("Standard account features are decent, but export functionality is locked behind enterprise plans.", "SaaS Dashboard", "Feature Requests", 3, "User Forum"),
        ("System uptime is impressive. We experienced 99.9% availability throughout the entire month.", "Cloud Service", "Reliability", 5, "Customer Interview"),
        ("Hidden fees were added at checkout without clear explanation. Very disappointing pricing policy.", "E-Commerce Platform", "Pricing", 1, "Trustpilot"),
        ("Received standard confirmation email after submitting request. Waiting for further update.", "Mobile App", "Customer Support", 3, "Email Survey"),
        ("The battery life exceeds expectations. Easily lasts two full days on a single charge.", "Electronics", "Product Quality", 5, "Amazon Review"),
        ("The analytics reports are difficult to export to PDF format. Please add one-click export.", "SaaS Dashboard", "Feature Requests", 2, "In-App Survey"),
        ("Prompt response from support agent, but the technical issue is still unresolved after 48 hours.", "Cloud Service", "Customer Support", 2, "Helpdesk Ticket")
    ]

    seeded_count = 0
    for text, prod, cat, rat, src in sample_items:
        fb = Feedback(
            feedback_text=text,
            product_or_service=prod,
            category=cat,
            rating=rat,
            source=src
        )
        db.add(fb)
        db.flush()

        res = analyze_single_feedback(text, rating=rat)
        sa = SentimentAnalysis(
            feedback_id=fb.id,
            sentiment=res["sentiment"],
            confidence_score=res["confidence_score"],
            keywords=json.dumps(res["keywords"]),
            detected_topic=res["detected_topic"],
            explanation=res["explanation"]
        )
        db.add(sa)
        seeded_count += 1

    db.commit()
    sync_improvement_issues(db)
    return {"status": "success", "message": f"Successfully seeded {seeded_count} sample feedback entries.", "seeded_count": seeded_count}
