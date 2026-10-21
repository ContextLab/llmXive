"""
Tests for the FastAPI interface stubs and session initialization.
Ensures that the /init_session endpoint returns a valid counterbalanced order,
and that the /edit endpoints for both the structured harness and chat interface
acknowledge requests with a 200 OK response.
"""

from fastapi.testclient import TestClient

from src.interfaces.structured_harness import app as structured_app
from src.interfaces.chat_interface import app as chat_app


def test_init_session_structured():
    """
    Verify that the session initialization endpoint returns a JSON payload
    containing an 'order' list with both interface identifiers.
    """
    client = TestClient(structured_app)
    response = client.post("/init_session", json={"participant_id": "test_user"})
    assert response.status_code == 200, "Expected 200 OK from /init_session"
    data = response.json()
    assert "order" in data, "Response JSON must contain 'order'"
    order = data["order"]
    assert isinstance(order, list), "'order' should be a list"
    assert set(order) == {"structured", "chat"}, "Order must contain both interface identifiers"
    assert len(order) == 2, "Order list must have exactly two elements"


def test_init_session_chat():
    """
    The same /init_session endpoint should be available on the chat interface app.
    """
    client = TestClient(chat_app)
    response = client.post("/init_session", json={"participant_id": "test_user"})
    assert response.status_code == 200, "Expected 200 OK from /init_session on chat app"
    data = response.json()
    assert "order" in data
    assert set(data["order"]) == {"structured", "chat"}


def test_structured_edit_endpoint():
    """
    The structured harness /edit endpoint should acknowledge the request.
    """
    client = TestClient(structured_app)
    payload = {"figure_id": "figure_0", "edit_commands": []}
    response = client.post("/edit", json=payload)
    assert response.status_code == 200, "Expected 200 OK from structured /edit"
    data = response.json()
    assert data.get("status") == "ok", "Edit endpoint should return status 'ok'"


def test_chat_edit_endpoint():
    """
    The chat interface /edit endpoint should acknowledge the request.
    """
    client = TestClient(chat_app)
    payload = {"figure_id": "figure_0", "instruction": "make axis red"}
    response = client.post("/edit", json=payload)
    assert response.status_code == 200, "Expected 200 OK from chat /edit"
    data = response.json()
    assert data.get("status") == "ok", "Chat edit endpoint should return status 'ok'"