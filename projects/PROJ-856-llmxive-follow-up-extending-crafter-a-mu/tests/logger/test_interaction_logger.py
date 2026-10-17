"""
Unit tests for ``src.logger.interaction_logger``.

The test truncates the global log file, writes a couple of records using
``log_interaction`` and then verifies that the JSON‑Lines file contains the
expected entries with correct fields and types.
"""

import json
from pathlib import Path

import pytest

from src.logger.interaction_logger import LOG_PATH, log_interaction

@pytest.fixture(autouse=True)
def clean_log():
    """Ensure a fresh log file for each test run."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Truncate the file if it exists, otherwise create an empty one.
    LOG_PATH.write_text("", encoding="utf-8")
    yield
    # Clean up after the test – leave an empty file for subsequent runs.
    LOG_PATH.write_text("", encoding="utf-8")

def test_log_interaction_writes_valid_jsonl():
    participant = "test-participant"
    figure = "fig-001"
    interface = "structured"
    payload = {"action": "set_color", "target": "axis", "value": "red"}
    iteration = 1

    # Write the first record.
    log_interaction(
        participant_id=participant,
        figure_id=figure,
        interface=interface,
        payload=payload,
        iteration=iteration,
    )

    # Write a second record with a different iteration.
    log_interaction(
        participant_id=participant,
        figure_id=figure,
        interface=interface,
        payload={"action": "move", "dx": 10, "dy": -5},
        iteration=2,
    )

    # Read back the file and parse each line as JSON.
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2, "Two interaction records should have been written."

    records = [json.loads(line) for line in lines]

    # Basic schema checks for both records.
    for rec in records:
        assert isinstance(rec["timestamp_ms"], int), "timestamp_ms must be an integer"
        assert rec["participant_id"] == participant
        assert rec["figure_id"] == figure
        assert rec["interface"] == interface
        assert isinstance(rec["iteration"], int) and rec["iteration"] >= 1
        assert isinstance(rec["payload"], dict)

    # Verify that iteration numbers increment correctly.
    assert records[0]["iteration"] == 1
    assert records[1]["iteration"] == 2

    # Payload of the first record should match the input payload.
    assert records[0]["payload"] == payload