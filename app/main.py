from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import init_db
from app.routes.admin import router as admin_router
from app.routes.delivery import router as delivery_router
from app.routes.submissions import router as submissions_router
from app.routes.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title="FlyRank Embeddable Widget & Lead-Capture Platform",
    description="High-performance, hardened public lead capture engine with CORS, rate limiting, and geo fallback.",
    version="1.0.0",
    lifespan=lifespan
)

# Open CORS configuration for cross-origin widget embeds and submissions
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["Cache-Control", "Retry-After"]
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize validation errors to clean HTTP 400 JSON errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": "Malformed or invalid payload.",
            "details": exc.errors()
        }
    )

# Register route modules
app.include_router(delivery_router)
app.include_router(submissions_router)
app.include_router(admin_router)
app.include_router(dashboard_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "flyrank-widget-platform",
        "environment": settings.APP_ENV
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "FlyRank Embeddable Widget & Lead-Capture Platform API",
        "docs_url": "/docs",
        "health_url": "/health"
    }
