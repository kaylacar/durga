"""Smoke tests for Durga's /.well-known/ declarations."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from khoj.routers.well_known import well_known_router


CONTACT_EMAIL = "contactkaylacard" + "@" + "gmail.com"


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(well_known_router, prefix="/.well-known")
    return TestClient(app)


def test_agents_txt():
    client = _make_client()
    response = client.get("/.well-known/agents.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "Spec-Version: 1.0" in body
    assert "Generated-At:" in body
    assert "Site-Name: Durga" in body
    assert "chat-with-user" in body
    assert "search-user-content" in body
    assert "transcribe-audio" in body
    assert "generate-speech" in body
    assert CONTACT_EMAIL in body


def test_agents_json():
    client = _make_client()
    response = client.get("/.well-known/agents.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    data = response.json()
    assert data["specVersion"] == "1.0"
    assert data["site"]["name"] == "Durga"
    cap_ids = {c["id"] for c in data["capabilities"]}
    expected = {"chat-with-user", "search-user-content", "transcribe-audio", "generate-speech"}
    assert expected <= cap_ids
    assert "generatedAt" in data


def test_ai_txt():
    client = _make_client()
    response = client.get("/.well-known/ai.txt")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "Spec-Version: 1.0" in body
    assert "Generated-At:" in body
    assert "Training: deny" in body
    assert "Site-Name: Durga" in body


def test_ai_json():
    client = _make_client()
    response = client.get("/.well-known/ai.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    data = response.json()
    assert data["specVersion"] == "1.0"
    assert data["policy"]["training"] == "deny"
    assert data["site"]["name"] == "Durga"
    assert "generatedAt" in data


def test_agents_override(tmp_path, monkeypatch):
    custom = tmp_path / "custom-agents.txt"
    custom.write_text(
        "# custom\nSpec-Version: 1.0\nSite-Name: Override\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DURGA_AGENTS_TXT_PATH", str(custom))
    client = _make_client()
    response = client.get("/.well-known/agents.txt")
    assert response.status_code == 200
    assert "Site-Name: Override" in response.text
    assert "Generated-At:" in response.text


def test_ai_override(tmp_path, monkeypatch):
    custom = tmp_path / "custom-ai.txt"
    custom.write_text(
        "# custom\nSpec-Version: 1.0\nTraining: allow\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DURGA_AI_TXT_PATH", str(custom))
    client = _make_client()
    response = client.get("/.well-known/ai.txt")
    assert response.status_code == 200
    assert "Training: allow" in response.text


def test_missing_override_falls_back(monkeypatch):
    monkeypatch.setenv("DURGA_AGENTS_TXT_PATH", "/no/such/file.txt")
    client = _make_client()
    response = client.get("/.well-known/agents.txt")
    assert response.status_code == 200
    assert "Site-Name: Durga" in response.text
