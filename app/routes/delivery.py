from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.widget import Widget
from app.schemas.widget import PublicWidgetConfig
from app.config import settings

router = APIRouter(tags=["Widget Delivery (Public & Cached)"])

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@router.get("/widget.js")
def get_widget_script():
    """
    Serves the embeddable JavaScript bundle with long-lived cache headers
    representing a production CDN versioned asset.
    """
    script_path = STATIC_DIR / "widget.js"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Widget script not found")

    content = script_path.read_text(encoding="utf-8")
    return Response(
        content=content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=86400, immutable",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/widgets/{widget_id}/config", response_model=PublicWidgetConfig)
def get_widget_config(
    widget_id: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Public, short-cached endpoint delivering dynamic form configuration
    to client-side widgets across any origin.
    """
    widget = db.query(Widget).filter(
        Widget.id == widget_id,
        Widget.is_active == True
    ).first()

    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active widget not found")

    # Short-lived cache headers for configuration freshness
    response.headers["Cache-Control"] = "public, max-age=60"
    response.headers["Access-Control-Allow-Origin"] = "*"

    base = settings.API_BASE_URL.rstrip("/")
    return PublicWidgetConfig(
        id=widget.id,
        title=widget.title,
        description=widget.description,
        widget_type=widget.widget_type,
        form_fields=widget.form_fields,
        button_text=widget.button_text,
        display_options=widget.display_options,
        submit_url=f"{base}/submissions"
    )
