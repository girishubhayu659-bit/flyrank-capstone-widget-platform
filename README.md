# FlyRank Capstone — Embeddable Widget & Lead-Capture Platform

A resilient, multi-tenant lead capture and embeddable widget platform built for the open internet. Customers configure custom widgets (newsletter signups, popovers, contact forms) and install them onto external websites with a single line of `<script>`. 

Inbound submissions from third-party client browsers are received across origins, validated at the boundary, protected against rate-limit bursts and automated bot spam, enriched with geolocation via a dual-provider fallback chain, safely stored in SQLite/PostgreSQL, and surfaced via an authenticated owner dashboard.

---

## 1. System Architecture

```
Visitor Browser (External Origin: http://localhost:5500)
    │
    │  1. <script src="http://localhost:8000/widget.js?id=w_123"></script>
    ├─────────────────────────────────────────────────────────────────► API Server
    │◄─── Cached Script (Cache-Control: public, max-age=86400) ─────────┤
    │
    │  2. GET /widgets/w_123/config (Cross-Origin)
    ├─────────────────────────────────────────────────────────────────► API Server
    │◄─── Widget Config JSON (Cache-Control: public, max-age=60) ───────┤
    │
    │  3. Form renders dynamically into page DOM
    │  4. Visitor fills inputs and submits
    │
    │  5. POST /submissions (Cross-Origin CORS Request)
    ├─────────────────────────────────────────────────────────────────► API Server
    │                                                                   │
    │                                                   [Boundary Size & Schema Guard]
    │                                                   <= 64KB, Pydantic validated (clean 4xx)
    │                                                                   │
    │                                                   [Abuse Defenses]
    │                                                   Sliding rate limit per IP & widget (429)
    │                                                   Honeypot bot field trap (rejects spam)
    │                                                                   │
    │                                                   [Geo Enrichment Fallback Chain]
    │                                                   ip-api.com ──(fails)──► ipapi.co ──(fails)──► Degrade to null
    │                                                                   │
    │                                                   [Safe Persistence & Isolation]
    │                                                   Stored with tenant_id & widget_id
    │                                                   │
    │                                                   [Fault-Tolerant Side Effect]
    │                                                   Email confirmation / webhook trigger
    │                                                   (Side effect failure never blocks 201)
    │                                                                   │
    │◄─── HTTP 201 Created {"success": true, "id": "sub_xyz"} ──────────┤
```

---

## 2. Quickstart (One Documented Command)

### Prerequisites
- Python 3.10+ installed

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Seed Demo Data
Populates a demo tenant (`Acme Corp`, API key `flyrank_sec_demo_key_123`), sample widgets, and initial submissions:
```bash
python scripts/seed_demo.py
```

### Step 3: Run the API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 3. Testing the Live Cross-Origin Customer Site

To experience the embed snippet running on an external domain:

1. Open a second terminal window and serve the `test-site/` directory on port `5500`:
   ```bash
   python -m http.server 5500 --directory test-site
   ```
2. Open [http://localhost:5500](http://localhost:5500) in your web browser.
3. Observe the lead capture widget rendered in the bottom right corner loaded across origins from `http://localhost:8000`.
4. Submit the form to verify CORS preflight (`OPTIONS`) and successful `201 Created` ingestion.

---

## 4. Automated Verification Suite (Acceptance Probes)

Run the full automated test suite covering all 6 evaluation probes and multi-tenant security:
```bash
pytest tests/ -v
```

### Evaluator Probes Covered:
- **PROBE 1:** Valid cross-origin submission stored with 201 and visible via dashboard API.
- **PROBE 2:** Malformed and oversized payloads (> 64KB) rejected with clean 4xx errors, never 500.
- **PROBE 3:** Rapid burst triggers 429 Too Many Requests while legitimate traffic continues uninterrupted.
- **PROBE 4:** Geo provider fallback chain: Provider A (`ip-api.com`) down → Provider B (`ipapi.co`) answers → both down degrades gracefully to null without failure.
- **PROBE 5:** Fault-isolated side effects: throwing an email exception never rolls back database transactions.
- **PROBE 6:** Invisible honeypot field captures automated bot spam and rejects it immediately.

---

## 5. API Reference Summary

### Authenticated Admin & Dashboard API
Header: `Authorization: Bearer <tenant_api_key>` (Demo key: `flyrank_sec_demo_key_123`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/widgets` | Create widget & retrieve embed snippet |
| `GET` | `/api/v1/widgets` | List tenant's widgets (tenant-isolated) |
| `GET` | `/api/v1/widgets/{id}` | Inspect widget details |
| `PUT` | `/api/v1/widgets/{id}` | Update widget configuration |
| `DELETE` | `/api/v1/widgets/{id}` | Delete widget |
| `GET` | `/api/v1/dashboard/stats` | Inbound lead metrics, widget breakdown & geo stats |
| `GET` | `/api/v1/dashboard/submissions` | List tenant submissions with pagination |

### Public Ingestion & Delivery Endpoints
Open to public internet and external browser callers (`Access-Control-Allow-Origin: *`):

| Method | Endpoint | Cache-Control Header | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/widget.js` | `public, max-age=86400, immutable` | Versioned embed script bundle |
| `GET` | `/widgets/{id}/config` | `public, max-age=60` | Dynamic widget schema configuration |
| `OPTIONS` | `/submissions` | — | CORS Preflight authorization handler |
| `POST` | `/submissions` | — | Hardened submission receiver with rate limit & geo |

---

## 6. Honest Limitations

- **In-Memory Rate Limiting:** The default rate limiter uses an in-memory sliding window cache. In a multi-instance autoscaling production cluster, the rate limiter would need to be backed by a centralized Redis instance.
- **No Client Framework Dependencies:** The embeddable widget engine is crafted in vanilla JavaScript without React or Vue to ensure a <10KB bundle payload and zero host-page dependency conflicts. Complex multi-step wizards would require heavier client architectures.
- **Synchronous Geo Fallback:** Primary and secondary geo lookups run with a 3.0s timeout per provider. Under complete network partitions, inbound requests incur up to 6.0s latency before degrading gracefully to null. A background queue (e.g., Celery / Redis Streams) would be ideal for high-throughput enterprise scale.

---

## 7. Submission Pack Manifest

This repository includes all required evaluation pack documents:
- `capstone.yaml`: Machine-readable evaluation manifest with run, seed, and probe commands.
- `EVIDENCE.md`: Step-by-step verification proofs for all Section 6 requirements.
- `BUILDLOG.md`: Human engineering and AI collaboration log.
- `DESIGN.md`: Phase 1 architecture and API design specification.
- `.env.example`: Safe environment configuration template.
- `LICENSE`: MIT License.
