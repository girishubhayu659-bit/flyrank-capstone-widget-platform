import pytest
from app.services.rate_limiter import rate_limiter
from app.services.geo_enrichment import geo_service
from app.services.side_effects import side_effect_service

def test_probe_1_valid_cross_origin_submission(client, test_tenants):
    """
    PROBE 1 — POST a valid submission from a cross-origin simulation
    -> stored, 2xx (201), and visible via the dashboard API.
    """
    # 1. Test CORS preflight OPTIONS request
    preflight = client.options(
        "/submissions",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    assert preflight.status_code in (200, 204)
    assert preflight.headers.get("access-control-allow-origin") in ("*", "http://localhost:5500")
    assert "POST" in preflight.headers.get("access-control-allow-methods", "")

    # 2. Submit lead
    res = client.post(
        "/submissions",
        headers={
            "Origin": "http://localhost:5500",
            "User-Agent": "Mozilla/5.0 TestBrowser",
            "X-Forwarded-For": "8.8.8.8"
        },
        json={
            "widget_id": "widget-alpha-1",
            "data": {"email": "alex.morgan@test.com", "name": "Alex Morgan"},
            "hp_field": ""
        }
    )
    assert res.status_code == 201
    assert res.headers.get("access-control-allow-origin") in ("*", "http://localhost:5500")
    body = res.json()
    assert body["success"] is True
    submission_id = body["id"]

    # 3. Verify it is visible via the owner's dashboard API
    alpha_headers = {"Authorization": "Bearer alpha_secret_key_111"}
    dash_res = client.get("/api/v1/dashboard/stats", headers=alpha_headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["total_submissions"] >= 1

    list_res = client.get("/api/v1/dashboard/submissions", headers=alpha_headers)
    assert list_res.status_code == 200
    sub_ids = [s["id"] for s in list_res.json()]
    assert submission_id in sub_ids

def test_probe_2_malformed_and_oversized_payloads(client):
    """
    PROBE 2 — Send a malformed and an oversized payload
    -> clean 4xx JSON errors, never a 500.
    """
    # Malformed JSON / missing required fields
    res_bad = client.post(
        "/submissions",
        content=b"{invalid-json-payload-broken",
        headers={"Content-Type": "application/json"}
    )
    assert res_bad.status_code == 400
    assert res_bad.json()["detail"] == "Malformed JSON payload."

    # Missing required widget_id
    res_missing = client.post(
        "/submissions",
        json={"data": {"email": "test@test.com"}}
    )
    assert res_missing.status_code == 400

    # Oversized payload (> 64KB)
    huge_data = {"email": "test@test.com", "junk": "A" * 70000}
    res_oversized = client.post(
        "/submissions",
        json={"widget_id": "widget-alpha-1", "data": huge_data}
    )
    assert res_oversized.status_code == 413
    assert "exceeds maximum" in res_oversized.json()["detail"]

def test_probe_3_rate_limiting_burst(client, test_tenants):
    """
    PROBE 3 — Fire a burst of rapid submissions
    -> 429s appear, and a normal request right after still succeeds.
    """
    test_ip = "198.51.100.42"
    widget_id = "widget-alpha-1"

    # Reset test IP history
    rate_limiter.ip_history[test_ip] = []

    # Send rapid burst (burst_limit is 5)
    statuses = []
    for _ in range(7):
        res = client.post(
            "/submissions",
            headers={"X-Forwarded-For": test_ip},
            json={
                "widget_id": widget_id,
                "data": {"email": "burst@test.com"},
                "hp_field": ""
            }
        )
        statuses.append(res.status_code)

    # Confirm 429 appeared in the burst
    assert 429 in statuses

    # Confirm a legitimate request from another IP still succeeds immediately!
    other_ip = "198.51.100.99"
    res_legit = client.post(
        "/submissions",
        headers={"X-Forwarded-For": other_ip},
        json={
            "widget_id": widget_id,
            "data": {"email": "legitimate@test.com"},
            "hp_field": ""
        }
    )
    assert res_legit.status_code == 201
    assert res_legit.json()["success"] is True

def test_probe_4_geo_provider_fallback_chain(client, test_tenants):
    """
    PROBE 4 — Disable geo provider A -> next submission is stored, enriched by provider B.
    Disable both -> stored anyway, without geo (degrade, never fail).
    """
    widget_id = "widget-alpha-1"
    geo_service.mock_mode = True

    try:
        # Case 1: Disable Provider A -> Provider B answers
        geo_service.provider_a_enabled = False
        geo_service.provider_b_enabled = True

        res_b = client.post(
            "/submissions",
            headers={"X-Forwarded-For": "198.51.100.1"},
            json={"widget_id": widget_id, "data": {"email": "provider_b@test.com"}, "hp_field": ""}
        )
        assert res_b.status_code == 201
        assert res_b.json()["enriched_geo"]["provider"] == "ipapi.co"
        assert res_b.json()["enriched_geo"]["city"] == "Berlin"

        # Case 2: Disable BOTH Provider A and Provider B -> Degrade gracefully to None
        geo_service.provider_a_enabled = False
        geo_service.provider_b_enabled = False

        res_none = client.post(
            "/submissions",
            headers={"X-Forwarded-For": "198.51.100.2"},
            json={"widget_id": widget_id, "data": {"email": "no_provider@test.com"}, "hp_field": ""}
        )
        assert res_none.status_code == 201
        assert res_none.json()["success"] is True
        assert res_none.json()["enriched_geo"]["provider"] is None
        assert res_none.json()["enriched_geo"]["country"] is None
    finally:
        # Restore default providers and mock mode
        geo_service.provider_a_enabled = True
        geo_service.provider_b_enabled = True
        geo_service.mock_mode = False

def test_probe_5_safe_side_effects_failure_tolerance(client, test_tenants):
    """
    PROBE 5 — Force the email/webhook side effect to throw
    -> the submission still returns success (201) and is stored.
    """
    side_effect_service.simulate_failure = True

    res = client.post(
        "/submissions",
        headers={"X-Forwarded-For": "198.51.100.3"},
        json={
            "widget_id": "widget-alpha-1",
            "data": {"email": "fault_test@test.com"},
            "hp_field": ""
        }
    )
    # Submission MUST succeed despite side effect failure
    assert res.status_code == 201
    assert res.json()["success"] is True

    side_effect_service.simulate_failure = False

def test_probe_6_honeypot_bot_defense(client, test_tenants):
    """
    PROBE 6 — Fill the honeypot field like a bot would
    -> the submission is rejected or dropped without polluting database.
    """
    res = client.post(
        "/submissions",
        json={
            "widget_id": "widget-alpha-1",
            "data": {"email": "spambot@viagra-deals.com"},
            "hp_field": "I am a malicious bot filling all form fields"
        }
    )
    assert res.status_code == 400
    assert "Spam submission rejected" in res.json()["detail"]
