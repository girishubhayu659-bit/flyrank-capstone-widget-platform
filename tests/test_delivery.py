import pytest

def test_widget_js_delivery_and_caching(client):
    """Widget script delivery serves versioned bundle with long-lived caching."""
    res = client.get("/widget.js")
    assert res.status_code == 200
    assert "application/javascript" in res.headers["content-type"]
    assert "public, max-age=86400, immutable" in res.headers["cache-control"]
    assert res.headers.get("access-control-allow-origin") == "*"
    assert "FlyRank Widget" in res.text

def test_public_widget_config_delivery(client, test_tenants):
    """Public config delivers small payload with short-lived cache headers."""
    res = client.get("/widgets/widget-alpha-1/config")
    assert res.status_code == 200
    assert "public, max-age=60" in res.headers["cache-control"]
    assert res.headers.get("access-control-allow-origin") == "*"

    body = res.json()
    assert body["id"] == "widget-alpha-1"
    assert body["title"] == "Alpha Newsletter"
    assert body["button_text"] == "Sign Up"
    assert body["submit_url"].endswith("/submissions")

def test_inactive_or_missing_widget_config(client):
    """Missing or inactive widgets return 404."""
    res = client.get("/widgets/non-existent-widget-999/config")
    assert res.status_code == 404
