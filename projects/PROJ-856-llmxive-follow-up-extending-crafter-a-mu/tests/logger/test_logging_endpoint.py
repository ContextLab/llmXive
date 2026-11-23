"""
test_logging_endpoint.py
------------------------

Integration tests for the FastAPI ``/log_interaction`` endpoint.
The tests verify that a POST request creates a line in the
``data/logs/interactions.jsonl`` file that conforms to the contract
schema and that the optional ``status`` field is added when the
elapsed time exceeds the abort threshold.
"""

import json

from fastapi.testclient import TestClient

# Import the FastAPI app
from src.interfaces.logging_endpoint import app

# Import the logger module directly (no __init__ needed)
import src.logger.interaction_logger as interaction_logger


def _reset_logger():
    """Helper to put the logger into a deterministic state and clear the file."""
    interaction_logger.set_deterministic(True)
    interaction_logger.clear_logs()
    # Restore the normal abort threshold after each test
    interaction_logger._ABORT_THRESHOLD_MS = 15 * 60 * 1000


def test_log_interaction_writes_entry():
    _reset_logger()
    client = TestClient(app)

    payload = {
        "participant_id": "p1",
        "figure_id": "f1",
        "interface": "structured",
        "payload": {"edit": "set_color('axis','red')"},
        "iteration": 1,
        "subjective_load": 42,
    }

    response = client.post("/log_interaction", json=payload)
    assert response.status_code == 200

    # Load the single line that should have been written
    log_path = interaction_logger.LOG_PATH
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1, "Exactly one log line should be present"

    record = json.loads(lines[0])
    assert record["participant_id"] == "p1"
    assert record["figure_id"] == "f1"
    assert record["interface"] == "structured"
    assert record["subjective_load"] == 42
    # The abort status should *not* be present for a normal entry
    assert "status" not in record


def test_log_interaction_aborted_status():
    _reset_logger()
    # Force the abort threshold to zero so any elapsed time triggers abort
    interaction_logger._ABORT_THRESHOLD_MS = 0

    client = TestClient(app)

    payload = {
        "participant_id": "p2",
        "figure_id": "f2",
        "interface": "chat",
        "payload": {"message": "make axis red"},
        "iteration": 1,
        "subjective_load": 10,
    }

    response = client.post("/log_interaction", json=payload)
    assert response.status_code == 200

    record = json.loads(interaction_logger.LOG_PATH.read_text(encoding="utf-8").strip())
    assert record["status"] == "aborted"
    # Clean up: restore the original threshold for subsequent tests
    interaction_logger._ABORT_THRESHOLD_MS = 15 * 60 * 1000