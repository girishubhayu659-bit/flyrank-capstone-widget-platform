import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class SideEffectService:
    def __init__(self):
        self.simulate_failure = settings.SIMULATE_SIDE_EFFECT_FAILURE
        self.dispatched_events: list[dict] = []

    def dispatch_confirmation(
        self,
        submission_id: str,
        widget_title: str,
        recipient_email: Optional[str],
        data: dict,
        force_fail: bool = False
    ) -> bool:
        """
        Executes confirmation notification / email.
        Enforces strict fault-isolation: secondary action failures MUST NEVER
        abort or roll back the primary submission storage.
        """
        try:
            if force_fail or self.simulate_failure:
                raise RuntimeError("Simulated side-effect failure (SMTP timeout / webhook unavailable)")

            event = {
                "submission_id": submission_id,
                "widget_title": widget_title,
                "recipient_email": recipient_email or "unknown@domain.com",
                "data": data,
                "status": "delivered"
            }
            self.dispatched_events.append(event)
            logger.info(f"[SIDE EFFECT] Confirmation sent for submission {submission_id} to {recipient_email}")
            return True
        except Exception as exc:
            # Fault isolation: Catch, log warning, do NOT re-raise
            logger.warning(f"[SAFE SIDE EFFECT RECOVERY] Secondary action failed: {exc}. Primary submission remains safe.")
            return False

side_effect_service = SideEffectService()
