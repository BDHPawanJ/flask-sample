def test_health_route(client):
    """Ensure health endpoint returns OK payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
