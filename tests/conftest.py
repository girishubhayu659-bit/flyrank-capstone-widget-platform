import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Create a single shared in-memory SQLite database using StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from app.database import Base, get_db
from app.main import app
from app.models.tenant import Tenant
from app.models.widget import Widget
from app.models.submission import Submission

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_tenants(db_session):
    # Tenant Alpha
    t_alpha = db_session.query(Tenant).filter(Tenant.id == "tenant-alpha").first()
    if not t_alpha:
        t_alpha = Tenant(id="tenant-alpha", name="Alpha Corp", api_key="alpha_secret_key_111")
        db_session.add(t_alpha)

    # Tenant Beta
    t_beta = db_session.query(Tenant).filter(Tenant.id == "tenant-beta").first()
    if not t_beta:
        t_beta = Tenant(id="tenant-beta", name="Beta LLC", api_key="beta_secret_key_222")
        db_session.add(t_beta)

    # Widgets
    w_alpha = db_session.query(Widget).filter(Widget.id == "widget-alpha-1").first()
    if not w_alpha:
        w_alpha = Widget(
            id="widget-alpha-1",
            tenant_id="tenant-alpha",
            title="Alpha Newsletter",
            widget_type="signup_form",
            form_fields=[{"name": "email", "label": "Email", "type": "email", "required": True}],
            button_text="Sign Up",
            display_options={},
            is_active=True
        )
        db_session.add(w_alpha)

    w_beta = db_session.query(Widget).filter(Widget.id == "widget-beta-1").first()
    if not w_beta:
        w_beta = Widget(
            id="widget-beta-1",
            tenant_id="tenant-beta",
            title="Beta Survey",
            widget_type="popover",
            form_fields=[{"name": "email", "label": "Email", "type": "email", "required": True}],
            button_text="Send Feedback",
            display_options={},
            is_active=True
        )
        db_session.add(w_beta)

    db_session.commit()
    return {"alpha": t_alpha, "beta": t_beta, "w_alpha": w_alpha, "w_beta": w_beta}
