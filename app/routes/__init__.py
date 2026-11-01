from app.routes.admin import router as admin_router
from app.routes.delivery import router as delivery_router
from app.routes.submissions import router as submissions_router
from app.routes.dashboard import router as dashboard_router

__all__ = ["admin_router", "delivery_router", "submissions_router", "dashboard_router"]
