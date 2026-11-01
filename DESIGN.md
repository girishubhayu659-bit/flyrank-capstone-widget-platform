# System Architecture & Design Document (Phase 1 Gate)

## 1. Problem Statement & Scope

Modern SaaS businesses rely heavily on lead generation forms, newsletters, and contact widgets embedded across external websites, blogs, and landing pages. Building dedicated backend endpoints and JavaScript runners for each external domain is error-prone, insecure, and unmaintainable.

This platform provides an end-to-end embeddable lead capture engine:
1. **Tenants (Widget Owners)** create and manage customized widgets via an authenticated management API and copy a single line of HTML/JS snippet.
2. **Third-Party Client Websites** paste the `<script>` tag; the browser loads a cached script and dynamic JSON configuration across origins.
3. **External Visitors** submit data back to a hardened public API that safely catches untrusted public internet traffic with strict CORS policies, boundary validation, rate limiting, bot honeypot detection, multi-provider geo enrichment with automatic fallback, and fault-tolerant side effects.
4. **Owners** monitor inbound leads and geographical metrics through an authenticated dashboard API.

---

## 2. Explicit Non-Goals (Boundaries of Scope)

To maintain focus on core backend engineering, the following are explicit non-goals:
- **No WYSIWYG visual drag-and-drop form designer:** Forms are defined declaratively via structured JSON schemas.
- **No paid cloud CDN or external domain hosting:** Caching and cross-origin isolation are simulated and tested locally across distinct origins (`localhost:8000` vs `localhost:5500`).
- **No real third-party SMTP billing requirements:** Email confirmation executes as an asynchronous, safe side effect logged locally, focusing on fault isolation (secondary action failure must never compromise primary submission storage).

---

## 3. Data Model & Tenancy Isolation

The database architecture is designed with strict multi-tenancy enforced at the query layer.

```
+-------------------------------------------------------------+
|                           tenants                           |
+-------------------------------------------------------------+
| id          : UUID (PK)                                     |
| name        : VARCHAR(255)                                  |
| api_key     : VARCHAR(255) (Hashed token for auth)          |
| created_at  : TIMESTAMP WITH TIME ZONE                      |
+-------------------------------------------------------------+
                               |
                               | 1:N
                               v
+-------------------------------------------------------------+
|                           widgets                           |
+-------------------------------------------------------------+
| id          : UUID (PK)                                     |
| tenant_id   : UUID (FK -> tenants.id, INDEXED)              |
| title       : VARCHAR(255)                                  |
| description : TEXT                                          |
| widget_type : VARCHAR(50) (signup_form / cta / popover)     |
| form_fields : JSON (name, email, message, etc.)             |
| button_text : VARCHAR(100)                                  |
| display_opt : JSON (theme, position, delay)                 |
| is_active   : BOOLEAN (Default TRUE, INDEXED)               |
| created_at  : TIMESTAMP WITH TIME ZONE                      |
| updated_at  : TIMESTAMP WITH TIME ZONE                      |
+-------------------------------------------------------------+
                               |
                               | 1:N
                               v
+-------------------------------------------------------------+
|                         submissions                         |
+-------------------------------------------------------------+
| id          : UUID (PK)                                     |
| widget_id   : UUID (FK -> widgets.id, INDEXED)              |
| tenant_id   : UUID (FK -> tenants.id, INDEXED)              |
| data        : JSON (Validated user form inputs)             |
| ip_address  : VARCHAR(45)                                   |
| user_agent  : TEXT                                          |
| geo_country : VARCHAR(100) (Nullable)                       |
| geo_city    : VARCHAR(100) (Nullable)                       |
| geo_provider: VARCHAR(50) (Nullable, 'ip-api' / 'ipapi.co') |
| submitted_at: TIMESTAMP WITH TIME ZONE (INDEXED)            |
+-------------------------------------------------------------+
```

### Multi-Tenant Query Isolation Guarantee:
Every query in the Admin and Dashboard APIs strictly includes `WHERE tenant_id = :current_tenant_id`. Tenant A can never read, update, delete, or aggregate Tenant B's widgets or submissions.

---

## 4. API Contracts across Three Request Paths

### Path 1: Widget Owner (Authenticated Admin & Dashboard API)
Requires `Authorization: Bearer <tenant_api_key>`.

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/widgets` | Create a new widget; returns embed snippet | 201, 400, 401 |
| `GET` | `/api/v1/widgets` | List all widgets owned by authenticated tenant | 200, 401 |
| `GET` | `/api/v1/widgets/{id}` | Retrieve specific widget configuration | 200, 401, 404 |
| `PUT` | `/api/v1/widgets/{id}` | Update widget configuration | 200, 400, 401, 404 |
| `DELETE` | `/api/v1/widgets/{id}` | Deactivate or delete widget | 204, 401, 404 |
| `GET` | `/api/v1/dashboard/stats` | Analytics (counts, per-widget totals, geo breakdown) | 200, 401 |
| `GET` | `/api/v1/dashboard/submissions` | List submissions with filtering & pagination | 200, 401 |

### Path 2: Customer Website (Public, Cached Delivery)
Public endpoints callable by any origin (`*`).

| Method | Endpoint | Description | Cache-Control Header |
| :--- | :--- | :--- | :--- |
| `GET` | `/widget.js` | Embed script loader (versioned bundle) | `public, max-age=86400, immutable` |
| `GET` | `/widgets/{id}/config` | Public widget schema & styling rules | `public, max-age=60` |

### Path 3: Website Visitor (Public, Hardened Ingestion)
Callable across origins from visitor browsers.

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `OPTIONS` | `/submissions` | CORS Preflight check | 200 / 204 |
| `POST` | `/submissions` | Ingest form data with honeypot & geo enrichment | 201, 400, 413, 429 |

---

## 5. End-to-End Embed & Ingestion Lifecycle

```
Visitor Browser (External Origin: http://localhost:5500)
    │
    │  1. <script src="http://localhost:8000/widget.js?id=w_123"></script>
    ├─────────────────────────────────────────────────────────────────► API Server
    │◄─── Returns cached widget.js (Cache-Control: max-age=86400) ──────┤
    │
    │  2. GET /widgets/w_123/config
    ├─────────────────────────────────────────────────────────────────► API Server
    │◄─── Returns widget config JSON (Cache-Control: max-age=60) ───────┤
    │
    │  3. Form dynamically renders inside Shadow DOM / container
    │  4. Visitor inputs email, name, clicks Submit
    │
    │  5. POST /submissions (Cross-Origin CORS Request)
    ├─────────────────────────────────────────────────────────────────► API Server
    │                                                                   │
    │                                                   [Boundary Validation]
    │                                                   Payload size <= 64KB? Valid JSON?
    │                                                   Missing required fields? -> 400 Bad Request
    │                                                                   │
    │                                                   [Abuse Protection]
    │                                                   Rate limit check per IP/widget? -> 429
    │                                                   Honeypot field (hp_field) filled? -> Drop/Reject
    │                                                                   │
    │                                                   [Geo Enrichment with Fallback]
    │                                                   Try Provider A (ip-api.com)
    │                                                     └─ Failed? -> Try Provider B (ipapi.co)
    │                                                     └─ Failed? -> Store with geo=null (Never fail)
    │                                                                   │
    │                                                   [Store in Database]
    │                                                   Row inserted with widget_id & tenant_id
    │                                                                   │
    │                                                   [Safe Side Effects]
    │                                                   Trigger confirmation email / event
    │                                                   (If side effect throws, catch & log)
    │                                                                   │
    │◄─── HTTP 201 Created {"success": true, "id": "sub_xyz"} ──────────┤
```

---

## 6. Failure Recovery & Graceful Degradation Strategy

1. **CORS Preflight:** Standardized FastAPI `CORSMiddleware` responding with `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: POST, OPTIONS, GET`, and `Access-Control-Allow-Headers: Content-Type, Authorization`.
2. **Deterministic Geo Provider Fallback Chain:**
   - Primary: `ip-api.com` (45 req/min, free, no key required).
   - Secondary: `ipapi.co` (~1,000 lookups/day, free tier).
   - Degrade to Null: If network is severed or both providers are down, the submission is recorded safely with `geo_country=None, geo_city=None`. The visitor gets `201 Created`.
3. **Safe Side Effect Isolation:**
   - Non-critical notifications (email / webhook dispatch) execute in a `try...except` block or FastAPI `BackgroundTasks`. An upstream SMTP timeout or webhook crash will never roll back or abort the database transaction.
