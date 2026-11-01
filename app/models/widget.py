import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Widget(Base):
    __tablename__ = "widgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    widget_type = Column(String(50), nullable=False, default="signup_form")  # signup_form, cta, popover
    form_fields = Column(JSON, nullable=False, default=list)  # list of field descriptors
    button_text = Column(String(100), nullable=False, default="Submit")
    display_options = Column(JSON, nullable=False, default=dict)  # theme, position, delay
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", back_populates="widgets")
    submissions = relationship("Submission", back_populates="widget", cascade="all, delete-orphan")

    @property
    def embed_snippet(self) -> str:
        from app.config import settings
        base = settings.API_BASE_URL.rstrip("/")
        return f'<script src="{base}/widget.js?id={self.id}"></script>'
