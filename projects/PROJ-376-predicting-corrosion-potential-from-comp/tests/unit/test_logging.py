"""
Unit test for the reproducible JSON‑line logging infrastructure (T003).
The test creates a temporary logger that writes to a temporary file,
emits a single log entry, and verifies that:
  1. The log file is created.
  2. The file contains exactly one line.
  3. The line is valid JSON with the required keys.
"""
import json
from pathlib import Path

import pytest

# Import the logging utilities from the project package.
from utils.logging import setup_logger, DEFAULT_LOG_DIR, DEFAULT_LOG_FILE


@pytest.fixture
def temp_log_path(tmp_path):
    """
    Provide a temporary path for the log file.
    """
    return tmp_path / "pipeline_test.log"


def test_logging_creates_file_and_writes_json_line(temp_log_path):
    """
    Verify that logging via ``setup_logger`` creates the file and writes a
    correctly‑formatted JSON line.
    """
    # Create a logger that writes only to the temporary file (no console output).
    logger = setup_logger(
        name="test_logger",
        log_file=str(temp_log_path),
        console=False,
        level=10,  # DEBUG level to capture everything
    )

    # Emit a test message.
    test_msg = "Unit test log entry"
    logger.info(test_msg)

    # Ensure the file exists.
    assert temp_log_path.is_file(), f"Log file was not created at {temp_log_path}"

    # Read the file contents.
    lines = temp_log_path.read_text(encoding="utf-8").strip().splitlines()
    # There should be exactly one line for the single log entry.
    assert len(lines) == 1, f"Expected 1 log line, found {len(lines)}"

    # Parse the JSON line.
    try:
        record = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        pytest.fail(f"Log line is not valid JSON: {exc}")

    # Verify required fields are present.
    for key in ("timestamp", "logger", "level", "message"):
        assert key in record, f"Missing '{key}' in log record"

    # Basic sanity checks on field contents.
    assert record["logger"] == "test_logger"
    assert record["level"] == "INFO"
    assert record["message"] == test_msg
    # ``timestamp`` should be an ISO‑8601 string; a simple check is that it contains a 'T'.
    assert "T" in record["timestamp"], "Timestamp is not ISO‑8601 formatted"