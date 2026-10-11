from app.routers.feedback import router as feedback_router
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router

__all__ = ["feedback_router", "analytics_router", "reports_router", "settings_router"]
