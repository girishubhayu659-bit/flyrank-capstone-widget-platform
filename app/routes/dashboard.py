from collections import Counter
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.auth import get_current_tenant
from app.models.tenant import Tenant
from app.models.widget import Widget
from app.models.submission import Submission
from app.schemas.dashboard import DashboardStats
from app.schemas.submission import SubmissionDetail

router = APIRouter(prefix="/api/v1/dashboard", tags=["Owner Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Enforces tenant isolation
    widgets = db.query(Widget).filter(Widget.tenant_id == current_tenant.id).all()
    widget_ids = [w.id for w in widgets]
    widget_map = {w.id: w.title for w in widgets}

    submissions = db.query(Submission).filter(
        Submission.tenant_id == current_tenant.id
    ).order_by(desc(Submission.submitted_at)).all()

    total_submissions = len(submissions)
    total_widgets = len(widgets)
    active_widgets = sum(1 for w in widgets if w.is_active)

    # Submissions by widget
    by_widget_counts = Counter(s.widget_id for s in submissions)
    by_widget = [
        {"widget_id": wid, "title": widget_map.get(wid, "Unknown"), "count": cnt}
        for wid, cnt in by_widget_counts.items()
    ]

    # Geo breakdown
    geo_counts = Counter(s.geo_country or "Unknown" for s in submissions)
    geo_breakdown = [
        {"country": country, "count": cnt}
        for country, cnt in geo_counts.most_common(10)
    ]

    # Recent submissions preview
    recent = [
        {
            "id": s.id,
            "widget_id": s.widget_id,
            "widget_title": widget_map.get(s.widget_id, "Unknown"),
            "data": s.data,
            "geo_country": s.geo_country,
            "geo_city": s.geo_city,
            "geo_provider": s.geo_provider,
            "submitted_at": s.submitted_at.isoformat()
        }
        for s in submissions[:5]
    ]

    return DashboardStats(
        total_submissions=total_submissions,
        total_widgets=total_widgets,
        active_widgets=active_widgets,
        submissions_by_widget=by_widget,
        geo_breakdown=geo_breakdown,
        recent_submissions=recent
    )

@router.get("/submissions", response_model=list[SubmissionDetail])
def list_submissions(
    widget_id: str = Query(None, description="Filter by specific widget"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    query = db.query(Submission).filter(Submission.tenant_id == current_tenant.id)
    if widget_id:
        query = query.filter(Submission.widget_id == widget_id)
    submissions = query.order_by(desc(Submission.submitted_at)).offset(offset).limit(limit).all()
    return submissions
