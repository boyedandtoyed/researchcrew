"""Web layer tests for the ResearchCrew FastAPI app."""
from fastapi.testclient import TestClient

from researchcrew.web import app

client = TestClient(app)


def test_index_serves_ui() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "ResearchCrew" in r.text


def test_health_reports_mode() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # In the test env there is no real key → demo mode
    assert body["mode"] in ("demo", "live")


def test_sync_research_demo_returns_report() -> None:
    """Without an API key the sync endpoint returns a demo report."""
    r = client.post("/api/research/sync", json={"topic": "test topic abc"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"]
    assert isinstance(body["findings"], list) and len(body["findings"]) >= 1
    assert "topic" in str(body).lower()


def test_streaming_research_emits_events() -> None:
    """The SSE endpoint emits plan/finding/report/done frames."""
    with client.stream(
        "POST", "/api/research", json={"topic": "transformers"}
    ) as r:
        assert r.status_code == 200
        text = "".join(chunk for chunk in r.iter_text())
    assert "event: plan" in text
    assert "event: report" in text
    assert "event: done" in text
