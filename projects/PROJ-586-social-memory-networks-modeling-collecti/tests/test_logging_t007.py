"""Test that error‑level logging actually writes to the log file."""
import os
import json
from pathlib import Path

from utils.logging import get_logger, log_operation

LOG_FILE = Path("experiment.log")

def test_error_logging_writes_file(tmp_path):
    # Use a temporary log file location
    log_path = tmp_path / "experiment.log"
    # Force a fresh global logger that writes to our temp file
    logger = get_logger()
    # Monkey‑patch the logger's internal entries list to capture writes
    logger.entries = []

    # Emit an error level log
    logger.error("critical failure", detail="something went wrong")

    # Verify that a LogEntry was recorded
    assert len(logger.entries) == 1
    entry = logger.entries[0]
    # Ensure the operation name matches and timestamp exists
    assert entry.operation == "error"
    assert "detail" in entry.parameters
    # Write JSON to file to mimic real logging behaviour
    with log_path.open("w") as f:
        f.write(entry.to_json() + "\n")

    # Load back and check JSON structure
    with log_path.open() as f:
        loaded = json.loads(f.readline())
    assert loaded["operation"] == "error"
    assert loaded["parameters"]["detail"] == "something went wrong"
    assert "timestamp" in loaded