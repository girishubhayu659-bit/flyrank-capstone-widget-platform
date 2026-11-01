from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SubmissionCreate(BaseModel):
    widget_id: str = Field(..., min_length=1, description="Target widget identifier")
    data: dict[str, Any] = Field(..., description="Form key-value inputs")
    hp_field: Optional[str] = Field(default="", description="Bot honeypot field - must be left empty")

class SubmissionResponse(BaseModel):
    success: bool
    id: str
    message: str
    enriched_geo: Optional[dict[str, Optional[str]]] = None

class SubmissionDetail(BaseModel):
    id: str
    widget_id: str
    tenant_id: str
    data: dict[str, Any]
    ip_address: str
    user_agent: Optional[str] = None
    geo_country: Optional[str] = None
    geo_city: Optional[str] = None
    geo_provider: Optional[str] = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
