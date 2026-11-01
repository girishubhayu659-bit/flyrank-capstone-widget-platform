from typing import Any
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_submissions: int
    total_widgets: int
    active_widgets: int
    submissions_by_widget: list[dict[str, Any]]
    geo_breakdown: list[dict[str, Any]]
    recent_submissions: list[dict[str, Any]]
