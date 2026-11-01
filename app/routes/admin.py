from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_tenant
from app.models.tenant import Tenant
from app.models.widget import Widget
from app.schemas.widget import WidgetCreate, WidgetUpdate, WidgetResponse
from app.config import settings

router = APIRouter(prefix="/api/v1/widgets", tags=["Widget Management (Admin)"])

def generate_embed_snippet(widget_id: str) -> str:
    base = settings.API_BASE_URL.rstrip("/")
    return f'<script src="{base}/widget.js?id={widget_id}"></script>'

@router.post("", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
def create_widget(
    payload: WidgetCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    widget = Widget(
        tenant_id=current_tenant.id,
        title=payload.title,
        description=payload.description,
        widget_type=payload.widget_type,
        form_fields=[f.model_dump() for f in payload.form_fields],
        button_text=payload.button_text,
        display_options=payload.display_options,
        is_active=payload.is_active
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)

    res = WidgetResponse.model_validate(widget)
    res.embed_snippet = generate_embed_snippet(widget.id)
    return res

@router.get("", response_model=list[WidgetResponse])
def list_widgets(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Enforces strict multi-tenant isolation
    widgets = db.query(Widget).filter(Widget.tenant_id == current_tenant.id).all()
    results = []
    for w in widgets:
        r = WidgetResponse.model_validate(w)
        r.embed_snippet = generate_embed_snippet(w.id)
        results.append(r)
    return results

@router.get("/{widget_id}", response_model=WidgetResponse)
def get_widget(
    widget_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    # Enforces tenant isolation: tenant A cannot inspect tenant B's widgets
    widget = db.query(Widget).filter(
        Widget.id == widget_id,
        Widget.tenant_id == current_tenant.id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    r = WidgetResponse.model_validate(widget)
    r.embed_snippet = generate_embed_snippet(widget.id)
    return r

@router.put("/{widget_id}", response_model=WidgetResponse)
def update_widget(
    widget_id: str,
    payload: WidgetUpdate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(
        Widget.id == widget_id,
        Widget.tenant_id == current_tenant.id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    if payload.title is not None:
        widget.title = payload.title
    if payload.description is not None:
        widget.description = payload.description
    if payload.widget_type is not None:
        widget.widget_type = payload.widget_type
    if payload.form_fields is not None:
        widget.form_fields = [f.model_dump() for f in payload.form_fields]
    if payload.button_text is not None:
        widget.button_text = payload.button_text
    if payload.display_options is not None:
        widget.display_options = payload.display_options
    if payload.is_active is not None:
        widget.is_active = payload.is_active

    db.commit()
    db.refresh(widget)

    r = WidgetResponse.model_validate(widget)
    r.embed_snippet = generate_embed_snippet(widget.id)
    return r

@router.delete("/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(
    widget_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(
        Widget.id == widget_id,
        Widget.tenant_id == current_tenant.id
    ).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found")

    db.delete(widget)
    db.commit()
    return None
