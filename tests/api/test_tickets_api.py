from datetime import datetime, timedelta

import pytest

pytestmark = pytest.mark.api


def create(client, title="Laptop does not start", priority="HIGH", description=""):
    return client.post("/api/tickets", json={"title": title, "priority": priority, "description": description})


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_create_ticket(client):
    response = create(client, priority="CRITICAL")
    ticket = response.get_json()

    assert response.status_code == 201
    assert ticket["id"] == 1
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "CRITICAL"
    created = datetime.fromisoformat(ticket["created_at"])
    due = datetime.fromisoformat(ticket["due_at"])
    assert due - created == timedelta(hours=4)
    assert ticket["overdue"] is False


@pytest.mark.parametrize("body, message", [
    ({"title": "abc"}, "title must be 5-100 characters"),
    ({"title": "Valid title", "priority": "URGENT"}, "priority must be one of"),
    (None, "request body must be a JSON object"),
])
def test_create_with_invalid_data_returns_400(client, body, message):
    response = client.post("/api/tickets", json=body) if body is not None \
        else client.post("/api/tickets", data="not json", content_type="text/plain")

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_get_ticket_and_unknown_ticket(client):
    create(client)
    assert client.get("/api/tickets/1").status_code == 200
    assert client.get("/api/tickets/999").status_code == 404


def test_filter_by_status_and_priority(client):
    create(client, title="Ticket one", priority="LOW")
    create(client, title="Ticket two", priority="HIGH")
    create(client, title="Ticket three", priority="HIGH")
    client.patch("/api/tickets/3", json={"status": "IN_PROGRESS"})

    assert [t["id"] for t in client.get("/api/tickets?priority=high").get_json()] == [2, 3]
    assert [t["id"] for t in client.get("/api/tickets?status=OPEN").get_json()] == [1, 2]
    assert [t["id"] for t in client.get("/api/tickets?status=IN_PROGRESS&priority=HIGH").get_json()] == [3]


@pytest.mark.parametrize("query", ["status=DONE", "priority=URGENT"])
def test_invalid_filter_returns_400(client, query):
    assert client.get(f"/api/tickets?{query}").status_code == 400


def test_full_ticket_lifecycle_with_reopen(client):
    create(client)
    for status in ["IN_PROGRESS", "RESOLVED", "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        response = client.patch("/api/tickets/1", json={"status": status})
        assert response.status_code == 200, status
        assert response.get_json()["status"] == status


def test_invalid_transition_returns_409_and_keeps_status(client):
    create(client)
    response = client.patch("/api/tickets/1", json={"status": "RESOLVED"})   # OPEN -> RESOLVED not allowed

    assert response.status_code == 409
    assert "cannot change from OPEN to RESOLVED" in response.get_json()["error"]
    assert client.get("/api/tickets/1").get_json()["status"] == "OPEN"


def test_unknown_status_returns_400(client):
    create(client)
    assert client.patch("/api/tickets/1", json={"status": "DONE"}).status_code == 400


def test_change_status_of_unknown_ticket_returns_404(client):
    assert client.patch("/api/tickets/42", json={"status": "CLOSED"}).status_code == 404


def test_delete_ticket(client):
    create(client)
    assert client.delete("/api/tickets/1").status_code == 204
    assert client.get("/api/tickets/1").status_code == 404
    assert client.delete("/api/tickets/1").status_code == 404


def test_html_in_title_is_stored_as_plain_text(client):
    title = "<script>alert('x')</script>"
    ticket = create(client, title=title).get_json()
    assert ticket["title"] == title
