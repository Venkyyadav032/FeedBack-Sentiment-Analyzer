import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi import FastAPI
from app.core.config import settings
from app.database.connection import engine, Base, get_db, DB_TYPE
from app.models import User, Feedback, SentimentAnalysis, ImprovementIssue
from app.routers import feedback_router, analytics_router, reports_router, settings_router
from app.routers.feedback import seed_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s...", settings.APP_NAME)
    # Ensure database tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully using %s engine.", DB_TYPE)
        
        # Auto seed sample data if empty
        db = next(get_db())
        try:
            if db.query(Feedback).count() == 0:
                logger.info("Database empty on startup. Automatically seeding sample feedback...")
                seed_sample_data(db)
        finally:
            db.close()
    except Exception as e:
        logger.error("Database initialization error: %s", str(e))
        
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    description="Sentiment Analysis and Feedback Intelligence System REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware Setup
origins = settings.cors_origins_list
logger.info("Configured CORS origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(feedback_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(settings_router)

# Health Check Endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "database": DB_TYPE.upper(),
        "version": "1.0.0"
    }

# Mount Frontend Static Directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)