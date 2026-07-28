"""
Unit test for the central logger.

The test verifies that a log entry written by ``src.utils.logger`` contains
the four mandatory fields required by ``contracts/pipeline_log.schema.yaml``:
``timestamp``, ``level``, ``message`` and ``schema_version``.
"""

import json
from pathlib import Path

import pytest

from src.utils.logger import get_logger


@pytest.fixture
def temporary_log_path(tmp_path: Path) -> Path:
    """
    Provide a fresh log file for each test.
    """
    return tmp_path / "pipeline_test.log"


def test_logger_writes_required_fields(temporary_log_path: Path):
    """
    Log a single message and assert the resulting JSON‑Line contains the
    required keys.
    """
    logger = get_logger(log_path=temporary_log_path)
    test_message = "unit‑test‑message"
    logger.info(test_message)

    # Ensure the file was actually created and contains exactly one line.
    lines = temporary_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1, "Expected exactly one log line"

    # Parse the JSON line.
    log_entry = json.loads(lines[0])

    # Required fields per the schema.
    required_fields = {"timestamp", "level", "message", "schema_version"}
    assert required_fields.issubset(log_entry.keys()), (
        f"Log entry missing required fields: {required_fields - set(log_entry.keys())}"
    )

    # Verify the values make sense.
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == test_message
    # ``schema_version`` is a static string; we accept any non‑empty value.
    assert isinstance(log_entry["schema_version"], str) and log_entry["schema_version"]

    # ``timestamp`` should be a valid ISO‑8601 string.  A simple sanity check:
    # it must contain a \"T\" separator and end with a timezone designator.
    timestamp = log_entry["timestamp"]
    assert "T" in timestamp, "Timestamp does not appear to be ISO‑8601"
    assert timestamp.endswith("Z") or ("+" in timestamp or "-" in timestamp), (
        "Timestamp does not contain timezone information"
    )