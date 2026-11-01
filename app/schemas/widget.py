from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class FormFieldSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Field name identifier")
    label: str = Field(..., min_length=1, description="Field label displayed to visitor")
    type: str = Field(default="text", description="Input type: text, email, textarea, etc.")
    required: bool = Field(default=True, description="Whether field is required")

class WidgetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: str = Field(default="signup_form", pattern="^(signup_form|cta|popover)$")
    form_fields: list[FormFieldSchema] = Field(default_factory=lambda: [
        FormFieldSchema(name="email", label="Your Email", type="email", required=True),
        FormFieldSchema(name="name", label="Your Name", type="text", required=False)
    ])
    button_text: str = Field(default="Submit", min_length=1, max_length=100)
    display_options: dict[str, Any] = Field(default_factory=lambda: {
        "theme": "light",
        "position": "bottom-right",
        "primary_color": "#2563eb"
    })
    is_active: bool = True

class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: Optional[str] = Field(None, pattern="^(signup_form|cta|popover)$")
    form_fields: Optional[list[FormFieldSchema]] = None
    button_text: Optional[str] = Field(None, min_length=1, max_length=100)
    display_options: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None

class WidgetResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: Optional[str] = None
    widget_type: str
    form_fields: list[dict[str, Any]]
    button_text: str
    display_options: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    embed_snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PublicWidgetConfig(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    widget_type: str
    form_fields: list[dict[str, Any]]
    button_text: str
    display_options: dict[str, Any]
    submit_url: str
