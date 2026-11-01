import pytest

def test_unauthenticated_request_rejected(client):
    """Requests without valid auth are rejected with 401."""
    res = client.get("/api/v1/widgets")
    assert res.status_code == 401

    res = client.post("/api/v1/widgets", json={"title": "Unauthorized"})
    assert res.status_code == 401

    res = client.get("/api/v1/widgets/widget-alpha-1", headers={"Authorization": "Bearer bad_key"})
    assert res.status_code == 401

def test_multi_tenant_crud_and_isolation(client, test_tenants):
    """Tenant A can create, read, update, delete widgets, but cannot touch Tenant B's widgets."""
    alpha_headers = {"Authorization": "Bearer alpha_secret_key_111"}
    beta_headers = {"Authorization": "Bearer beta_secret_key_222"}

    # 1. Tenant Alpha creates a widget
    create_res = client.post(
        "/api/v1/widgets",
        headers=alpha_headers,
        json={
            "title": "Alpha Product Launch Form",
            "widget_type": "signup_form",
            "form_fields": [
                {"name": "email", "label": "Work Email", "type": "email", "required": True}
            ],
            "button_text": "Notify Me"
        }
    )
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]
    assert "embed_snippet" in create_res.json()
    assert f"?id={created_id}" in create_res.json()["embed_snippet"]

    # 2. Tenant Alpha can retrieve it
    get_res = client.get(f"/api/v1/widgets/{created_id}", headers=alpha_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Alpha Product Launch Form"

    # 3. Tenant Beta CANNOT see or access Tenant Alpha's widget (Multi-tenant isolation)
    beta_get_res = client.get(f"/api/v1/widgets/{created_id}", headers=beta_headers)
    assert beta_get_res.status_code == 404

    # 4. Tenant Beta CANNOT update Tenant Alpha's widget
    beta_put_res = client.put(
        f"/api/v1/widgets/{created_id}",
        headers=beta_headers,
        json={"title": "Hacked Title"}
    )
    assert beta_put_res.status_code == 404

    # 5. Tenant Beta CANNOT delete Tenant Alpha's widget
    beta_del_res = client.delete(f"/api/v1/widgets/{created_id}", headers=beta_headers)
    assert beta_del_res.status_code == 404

    # 6. Tenant Alpha can update and delete their own widget
    alpha_put_res = client.put(
        f"/api/v1/widgets/{created_id}",
        headers=alpha_headers,
        json={"title": "Alpha Updated Launch Form"}
    )
    assert alpha_put_res.status_code == 200
    assert alpha_put_res.json()["title"] == "Alpha Updated Launch Form"

    alpha_del_res = client.delete(f"/api/v1/widgets/{created_id}", headers=alpha_headers)
    assert alpha_del_res.status_code == 204
