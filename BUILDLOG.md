# BUILDLOG — Engineering Notes & AI Collaboration Log

This log documents the design decisions, automated tool usage, architectural debugging, and manual code refactoring during the construction of the FlyRank Embeddable Widget & Lead-Capture Platform.

---

## 1. Phase 1 — Architecture & Data Design

- **Where AI Assisted:**
  - Generating initial draft of `DESIGN.md` based on the capstone brief requirements.
  - Designing the multi-tenant schema relationships (`tenants` -> `widgets` -> `submissions`).
- **Where Human Engineering Intervened / Corrected:**
  - AI initially drafted single global rate limits. Corrected this to dual-axis rate limiting: per-IP and per-widget sliding windows to isolate tenants against shared IP attacks.
  - Added explicit indexing strategies on `(tenant_id, submitted_at)` and `(widget_id, is_active)` for O(1) multi-tenant lookups and fast dashboard aggregations.
  - Defined explicit non-goals (no heavy WYSIWYG builders, no paid external CDNs, no paid SMTP credentials).

---

## 2. Phase 2 — Public Hardening, CORS & Fallback Chains

- **Where AI Assisted:**
  - FastAPI router templates and Pydantic schema validation structures.
  - Async request size inspection logic for the 64KB boundary guard.
- **Where AI was Wrong / What Was Changed:**
  - **CORS Credentials vs Wildcard Mirroring:** AI initially assumed `Access-Control-Allow-Origin: *` works unconditionally with `allow_credentials=True`. Modern browser W3C standards reject wildcard origins when credentials are transmitted. Refactored middleware and preflight handlers to mirror caller origins (e.g., `http://localhost:5500`) while maintaining wildcard fallback for simple public scripts.
  - **Pydantic v2 `ConfigDict` Migration:** AI generated legacy Pydantic v1 `class Config: from_attributes = True`. Upgraded to modern Pydantic v2 `model_config = ConfigDict(from_attributes=True)` to prevent deprecation warnings.
  - **SQLite In-Memory Test Isolation:** AI wrote `sqlite:///:memory:` in `conftest.py` without connection pooling, which wiped tables across separate test client threads (`OperationalError: no such table: widgets`). Refactored test engine to use SQLAlchemy's `StaticPool` to preserve schema state across the entire test session.
  - **Geo Fallback Determinism:** Real external geo APIs reject documentation IPs (RFC 5737). Implemented a deterministic mock mode switch in `GeoEnrichmentService` to satisfy Section 3 & 7 rules ("Mock the geo providers when you prove the fallback so it is deterministic").

---

## 3. Phase 3 — Delivery, Client-Side Engine & Dashboard

- **Where AI Assisted:**
  - Base template for the vanilla JavaScript widget script (`widget.js`).
  - Dashboard aggregation queries using Python `collections.Counter` and SQLAlchemy ordering.
- **Where Human Engineering Intervened / Corrected:**
  - Designed the bot defense honeypot: injected an off-screen, tab-indexed `-1` `<input name="hp_field">`. Legitimate humans never see or fill this field; automated web scrapers and bot crawlers populate every `<input>`, allowing zero-latency bot rejection with HTTP 400.
  - Tuned `Cache-Control` headers: `public, max-age=86400, immutable` for versioned bundle delivery, and `public, max-age=60` for public widget config.
  - Isolated side effects: wrapped confirmation triggers in a dedicated `try...except` boundary ensuring secondary notification failures can never abort database transactions.

---

## Code Ownership Statement
All logic, architectural boundaries, failure-handling mechanisms, and security invariants in this repository were reviewed, tested, and verified to pass all 6 Acceptance Probes defined in the FlyRank Backend Track Capstone Brief.
