"""
Integration tests for the interaction logger via the FastAPI edit endpoints.
These tests verify that a real HTTP request results in a correctly‑formatted
log entry and that the abort logic (15‑minute timeout) is applied.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.logger.interaction_logger import LOG_PATH, log_interaction, _ABORT_THRESHOLD_MS
from src.interfaces.structured_harness import app as structured_app
from src.interfaces.chat_interface import app as chat_app


@pytest.fixture(autouse=True)
def clean_log():
    """Ensure a fresh log file for each test run."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    yield
    LOG_PATH.write_text("", encoding="utf-8")


def _read_last_record():
    """Utility to read the most recent JSON‑L record from the log."""
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "Log file should contain at least one line"
    return json.loads(lines[-1])


def test_structured_edit_creates_log_entry():
    client = TestClient(structured_app)
    payload = {"action": "set_color", "target": "axis", "value": "red"}
    response = client.post(
        "/edit",
        json={
            "participant_id": "user-123",
            "figure_id": "fig-001",
            "interface": "structured",
            "payload": payload,
            "iteration": 1,
        },
    )
    assert response.status_code == 200
    
    rec = _read_last_record()
    assert rec["session_id"] == "user-123"
    assert rec["task_id"] == "fig-001"
    assert rec["mode"] == "structured"
    assert rec["iteration"] == 1
    # payload stored as a JSON‑encoded string
    assert json.loads(rec["payload"]) == payload
    # task_start_ms and task_end_ms must be present and equal for a single edit
    assert isinstance(rec["task_start_ms"], int)
    assert isinstance(rec["task_end_ms"], int)
    assert rec["task_start_ms"] == rec["task_end_ms"]
    # No abort status for a single quick edit
    assert "status" not in rec


def test_chat_edit_creates_log_entry():
    client = TestClient(chat_app)
    payload = {"utterance": "Make the axis red"}
    response = client.post(
        "/edit",
        json={
            "participant_id": "user-456",
            "figure_id": "fig-002",
            "interface": "chat",
            "payload": payload,
            "iteration": 1,
        },
    )
    assert response.status_code == 200
    
    rec = _read_last_record()
    assert rec["session_id"] == "user-456"
    assert rec["task_id"] == "fig-002"
    assert rec["mode"] == "chat"
    assert json.loads(rec["payload"]) == payload


def test_abort_status_is_recorded(monkeypatch):
    """
    Simulate a task that exceeds the 15‑minute threshold.
    The first call records the start time; the second call returns a
    timestamp far enough in the future to trigger the abort flag.
    """
    # Prepare a sequence of timestamps: 0 for the first call, then
    # _ABORT_THRESHOLD_MS + 1 for the second call.
    timestamps = iter([0, _ABORT_THRESHOLD_MS + 1])
    monkeypatch.setattr(
        "src.logger.interaction_logger._timestamp_ms",
        lambda: next(timestamps),
    )

    # First interaction (iteration 1)
    log_interaction(
        participant_id="user-abort",
        figure_id="fig-abort",
        interface="structured",
        payload={"action": "noop"},
        iteration=1,
    )
    # Second interaction (iteration 2) – should trigger abort
    log_interaction(
        participant_id="user-abort",
        figure_id="fig-abort",
        interface="structured",
        payload={"action": "noop"},
        iteration=2,
    )

    # The last log line must contain the abort status
    rec = _read_last_record()
    assert rec["session_id"] == "user-abort"
    assert rec["task_id"] == "fig-abort"
    assert rec["status"] == "aborted"
    # Ensure task_end_ms - task_start_ms exceeds the threshold
    assert rec["task_end_ms"] - rec["task_start_ms"] > _ABORT_THRESHOLD_MS


def test_multiple_iterations_increment():
    client = TestClient(structured_app)
    participant = "multi-user"
    figure = "multi-fig"
    payload = {"action": "increment"}

    # Send two sequential edits
    client.post(
        "/edit",
        json={
            "participant_id": participant,
            "figure_id": figure,
            "interface": "structured",
            "payload": payload,
            "iteration": 1,
        },
    )
    client.post(
        "/edit",
        json={
            "participant_id": participant,
            "figure_id": figure,
            "interface": "structured",
            "payload": payload,
            "iteration": 2,
        },
    )

    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    assert rec1["iteration"] == 1
    assert rec2["iteration"] == 2
    # task_start_ms should be the same for both records; task_end_ms should reflect the later timestamp
    assert rec1["task_start_ms"] == rec2["task_start_ms"]
    assert rec2["task_end_ms"] >= rec1["task_end_ms"]