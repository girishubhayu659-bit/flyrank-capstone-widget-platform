import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/platform.db")
    ALLOWED_ORIGINS: list[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    MAX_PAYLOAD_BYTES: int = int(os.getenv("MAX_PAYLOAD_BYTES", "65536"))
    
    # Geolocation fallback flags
    GEO_PROVIDER_A_ENABLED: bool = os.getenv("GEO_PROVIDER_A_ENABLED", "true").lower() == "true"
    GEO_PROVIDER_B_ENABLED: bool = os.getenv("GEO_PROVIDER_B_ENABLED", "true").lower() == "true"
    
    # Fault injection for evaluations
    SIMULATE_SIDE_EFFECT_FAILURE: bool = os.getenv("SIMULATE_SIDE_EFFECT_FAILURE", "false").lower() == "true"

settings = Settings()
