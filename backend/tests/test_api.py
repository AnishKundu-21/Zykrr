"""
Integration tests for the REST API.

Uses httpx.AsyncClient with ASGITransport so no real server is needed.
An in-memory SQLite DB is used per test run.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import engine, Base


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# POST /tickets/analyze
# ---------------------------------------------------------------------------


async def test_analyze_returns_201(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "App is down",
        "description": "Getting 500 errors, this is urgent",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Technical"
    assert data["priority"] == "P0"
    assert data["urgency"] is True
    assert 0 < data["confidence"] <= 1
    assert isinstance(data["keywords"], list)
    assert isinstance(data["custom_flags"], list)
    assert "id" in data
    assert "created_at" in data


async def test_analyze_billing_ticket(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "Wrong charge",
        "description": "I was overcharged on my subscription invoice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Billing"


async def test_analyze_security_escalation(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "Security issue",
        "description": "I think there has been a data breach in my account",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["priority"] == "P0"
    assert "security_escalation" in data["custom_flags"]


async def test_analyze_refund_escalation(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "Refund request",
        "description": "Please process my refund",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["priority"] in ("P0", "P1")
    assert "refund_detected" in data["custom_flags"]


async def test_analyze_validates_empty_subject(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "",
        "description": "Some description",
    })
    assert resp.status_code == 422


async def test_analyze_validates_empty_description(client):
    resp = await client.post("/tickets/analyze", json={
        "subject": "Subject",
        "description": "  ",
    })
    assert resp.status_code == 422


async def test_analyze_validates_missing_fields(client):
    resp = await client.post("/tickets/analyze", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /tickets
# ---------------------------------------------------------------------------


async def test_get_tickets_empty(client):
    resp = await client.get("/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tickets"] == []
    assert data["total"] == 0


async def test_get_tickets_returns_latest_first(client):
    for i in range(3):
        await client.post("/tickets/analyze", json={
            "subject": f"Ticket {i}",
            "description": "Some issue",
        })
    resp = await client.get("/tickets")
    assert resp.status_code == 200
    tickets = resp.json()["tickets"]
    assert len(tickets) == 3
    # Newest first
    ids = [t["id"] for t in tickets]
    assert ids == sorted(ids, reverse=True)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
