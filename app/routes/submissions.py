import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.widget import Widget
from app.models.submission import Submission
from app.schemas.submission import SubmissionCreate, SubmissionResponse
from app.services.rate_limiter import rate_limiter
from app.services.geo_enrichment import geo_service
from app.services.side_effects import side_effect_service
from app.config import settings

router = APIRouter(tags=["Public Submission Ingestion"])

@router.options("/submissions")
def handle_options_preflight():
    """Explicit CORS preflight responder for open internet browser clients."""
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS, GET",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )

@router.post("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_lead(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # Enable CORS on submission response
    response.headers["Access-Control-Allow-Origin"] = "*"

    # 1. Enforce payload size boundary (< 64KB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload exceeds maximum allowed size of {settings.MAX_PAYLOAD_BYTES} bytes."
        )

    # Read raw body
    body_bytes = await request.body()
    if len(body_bytes) > settings.MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload exceeds maximum allowed size of {settings.MAX_PAYLOAD_BYTES} bytes."
        )

    try:
        raw_json = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload."
        )

    # 2. Boundary validation with Pydantic
    try:
        payload = SubmissionCreate(**raw_json)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {exc}"
        )

    # 3. Client IP extraction
    client_ip = request.client.host if request.client else "127.0.0.1"
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        client_ip = x_forwarded.split(",")[0].strip()

    # 4. Abuse Protection: Rate limiting per IP and Widget
    rate_limiter.check_rate_limit(client_ip, payload.widget_id)

    # 5. Abuse Protection: Honeypot field inspection (bot detection)
    if payload.hp_field and payload.hp_field.strip():
        # Bot filled the invisible honeypot field -> reject / drop cleanly
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Spam submission rejected by bot defense."
        )

    # 6. Verify Target Widget Exists & Active
    widget = db.query(Widget).filter(
        Widget.id == payload.widget_id,
        Widget.is_active == True
    ).first()
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget not found or inactive."
        )

    # 7. Geolocation Enrichment with Fallback Chain (Provider A -> Provider B -> None)
    geo_country, geo_city, geo_provider = geo_service.enrich_ip(client_ip)

    # 8. Persist Submission Safely
    submission = Submission(
        widget_id=widget.id,
        tenant_id=widget.tenant_id,
        data=payload.data,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        geo_country=geo_country,
        geo_city=geo_city,
        geo_provider=geo_provider
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 9. Asynchronous Safe Side Effects (Email/Webhook)
    # Failure MUST NEVER rollback the primary submission
    recipient_email = payload.data.get("email") if isinstance(payload.data, dict) else None
    side_effect_service.dispatch_confirmation(
        submission_id=submission.id,
        widget_title=widget.title,
        recipient_email=recipient_email,
        data=payload.data
    )

    return SubmissionResponse(
        success=True,
        id=submission.id,
        message="Submission accepted and stored successfully.",
        enriched_geo={
            "country": geo_country,
            "city": geo_city,
            "provider": geo_provider
        }
    )
