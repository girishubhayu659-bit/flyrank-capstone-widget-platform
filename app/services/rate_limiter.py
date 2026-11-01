import time
from collections import defaultdict
from fastapi import HTTPException, status
from app.config import settings

class RateLimiter:
    """
    Sliding window in-memory rate limiter per IP and per Widget.
    Guarantees that a burst flood receives 429 Too Many Requests,
    while legitimate normal requests continue to be served.
    """
    def __init__(self, requests_per_minute: int = 20, burst_limit: int = 5, burst_window: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        self.ip_history = defaultdict(list)
        self.widget_history = defaultdict(list)

    def check_rate_limit(self, ip: str, widget_id: str):
        now = time.time()
        minute_ago = now - 60.0
        burst_ago = now - self.burst_window

        # Clean history older than 60s
        self.ip_history[ip] = [t for t in self.ip_history[ip] if t > minute_ago]
        self.widget_history[widget_id] = [t for t in self.widget_history[widget_id] if t > minute_ago]

        # Check burst window for this IP
        recent_burst = [t for t in self.ip_history[ip] if t > burst_ago]
        if len(recent_burst) >= self.burst_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests. Rate limit burst threshold exceeded. Please wait.",
                headers={"Retry-After": str(self.burst_window)}
            )

        # Check minute window for this IP
        if len(self.ip_history[ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests. Per-minute limit reached.",
                headers={"Retry-After": "60"}
            )

        # Record this request
        self.ip_history[ip].append(now)
        self.widget_history[widget_id].append(now)

rate_limiter = RateLimiter(
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst_limit=5,
    burst_window=10
)
