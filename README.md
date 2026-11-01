# FlyRank Capstone — Embeddable Widget & Lead-Capture Platform

> **Live Capstone Project · Backend Track**  
> A high-performance, resilient platform that enables customers to create embeddable widgets, distribute them via a single `<script>` tag, and securely ingest public internet submissions — with multi-tenant isolation, CORS handling, boundary validation, rate limiting, honeypot spam protection, IP geolocation enrichment with provider fallback, and asynchronous safe side effects.

---

## Project Status

- **Status:** In Progress (Phase 1: Architecture & Design)
- **Language / Framework:** Python 3.10+ / FastAPI
- **Database:** SQLite / PostgreSQL (Docker Compose)
- **Security:** Tenant isolation, CORS preflight handling, SlowAPI rate limiting, honeypot bot defense
- **Enrichment:** Dual-provider IP Geolocation fallback (`ip-api.com` → `ipapi.co` → graceful degradation)
- **Zero Cost Promise:** $0 budget, no credit card required.
