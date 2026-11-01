import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    widget_id = Column(String(36), ForeignKey("widgets.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    geo_country = Column(String(100), nullable=True)
    geo_city = Column(String(100), nullable=True)
    geo_provider = Column(String(50), nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    widget = relationship("Widget", back_populates="submissions")
    tenant = relationship("Tenant", back_populates="submissions")
