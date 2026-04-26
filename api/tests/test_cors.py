import importlib
import os

from fastapi.testclient import TestClient


def _reload_app():
    import main
    return importlib.reload(main).app


def test_cors_default_allows_any_origin(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    app = _reload_app()
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_respects_custom_origins(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://adipa-frontend.onrender.com",
    )
    app = _reload_app()
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://adipa-frontend.onrender.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://adipa-frontend.onrender.com"
    )


def test_cors_blocks_disallowed_origin(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://adipa-frontend.onrender.com",
    )
    app = _reload_app()
    client = TestClient(app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://malicious.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None
