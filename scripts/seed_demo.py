import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal, init_db
from app.models.tenant import Tenant
from app.models.widget import Widget
from app.models.submission import Submission

def seed():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Create or get Demo Tenant
        tenant = db.query(Tenant).filter(Tenant.id == "demo-tenant-1").first()
        if not tenant:
            tenant = Tenant(
                id="demo-tenant-1",
                name="Acme Corporation",
                api_key="flyrank_sec_demo_key_123"
            )
            db.add(tenant)
            db.commit()
            print("Created Demo Tenant (API Key: flyrank_sec_demo_key_123)")

        # 2. Create or get Demo Widget 1 (Newsletter)
        w1 = db.query(Widget).filter(Widget.id == "demo-widget-newsletter").first()
        if not w1:
            w1 = Widget(
                id="demo-widget-newsletter",
                tenant_id=tenant.id,
                title="Join Our Tech Newsletter",
                description="Get weekly backend tips, architecture teardowns, and engineering insights.",
                widget_type="signup_form",
                form_fields=[
                    {"name": "email", "label": "Email Address", "type": "email", "required": True},
                    {"name": "name", "label": "Your Name", "type": "text", "required": False}
                ],
                button_text="Subscribe Now",
                display_options={"theme": "light", "primary_color": "#2563eb", "position": "bottom-right"},
                is_active=True
            )
            db.add(w1)
            print("Created Demo Widget: demo-widget-newsletter")

        # 3. Create or get Demo Widget 2 (Contact Sales)
        w2 = db.query(Widget).filter(Widget.id == "demo-widget-contact").first()
        if not w2:
            w2 = Widget(
                id="demo-widget-contact",
                tenant_id=tenant.id,
                title="Contact Sales Team",
                description="Ready to scale? Connect with our enterprise solutions team.",
                widget_type="popover",
                form_fields=[
                    {"name": "name", "label": "Full Name", "type": "text", "required": True},
                    {"name": "email", "label": "Work Email", "type": "email", "required": True},
                    {"name": "message", "label": "Project Details", "type": "textarea", "required": True}
                ],
                button_text="Send Message",
                display_options={"theme": "dark", "primary_color": "#0f172a", "position": "bottom-left"},
                is_active=True
            )
            db.add(w2)
            print("Created Demo Widget: demo-widget-contact")

        db.commit()

        # 4. Seed initial submissions for dashboard analytics
        sub_count = db.query(Submission).filter(Submission.tenant_id == tenant.id).count()
        if sub_count == 0:
            sample_submissions = [
                Submission(
                    widget_id="demo-widget-newsletter",
                    tenant_id=tenant.id,
                    data={"email": "sarah.connor@cyberdyne.io", "name": "Sarah Connor"},
                    ip_address="8.8.8.8",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    geo_country="United States",
                    geo_city="Mountain View",
                    geo_provider="ip-api.com"
                ),
                Submission(
                    widget_id="demo-widget-newsletter",
                    tenant_id=tenant.id,
                    data={"email": "elena.rostova@berlin-tech.de", "name": "Elena Rostova"},
                    ip_address="134.119.0.1",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    geo_country="Germany",
                    geo_city="Berlin",
                    geo_provider="ipapi.co"
                ),
                Submission(
                    widget_id="demo-widget-contact",
                    tenant_id=tenant.id,
                    data={"name": "Kenji Sato", "email": "kenji@tokyo-robotics.jp", "message": "Inquiring about 500 seat enterprise license."},
                    ip_address="133.242.0.1",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64)",
                    geo_country="Japan",
                    geo_city="Tokyo",
                    geo_provider="ip-api.com"
                )
            ]
            db.add_all(sample_submissions)
            db.commit()
            print(f"Seeded {len(sample_submissions)} initial sample submissions for dashboard demo.")

        print("\nSeed completed successfully!")
        print(f"API Key for Acme Corp: flyrank_sec_demo_key_123")
        print(f"Demo Widget 1: demo-widget-newsletter")
        print(f"Demo Widget 2: demo-widget-contact")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
