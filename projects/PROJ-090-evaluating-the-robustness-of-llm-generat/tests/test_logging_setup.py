import json
import os
from pathlib import Path

import pytest

# Import the module under test
from code.utils import logging as logging_mod

LOG_FILE = Path("data/logs/app.log")

def test_setup_logger_creates_file_and_writes_json_line(tmp_path, monkeypatch):
    """
    Ensure that calling setup_logger() creates the expected log file
    and writes at least one well‑formed JSON line.
    """
    # Ensure a clean state: remove the file if it exists
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    # Call the function under test
    logger = logging_mod.setup_logger()

    # The logger should be an instance of logging.Logger
    assert isinstance(logger, type(logging_mod.logging.getLogger("test")))

    # The file must now exist
    assert LOG_FILE.exists(), "app.log was not created by setup_logger()"

    # Read the first line and verify it is valid JSON with expected keys
    with LOG_FILE.open("r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    assert first_line, "app.log is empty; no JSON line was written"

    try:
        entry = json.loads(first_line)
    except json.JSONDecodeError as e:
        pytest.fail(f"First line of app.log is not valid JSON: {e}")

    # Expected keys in the JSON log entry
    expected_keys = {"timestamp", "level", "logger", "message"}
    assert expected_keys.issubset(entry.keys()), f"Log entry missing keys: {expected_keys - set(entry.keys())}"

    # The message should match the initialization message
    assert entry["message"] == "app logger initialized"
    assert entry["logger"] == "app"
    assert entry["level"] == "INFO"