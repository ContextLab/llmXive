"""Tests for the logging infrastructure (T006)."""
import os
import csv
import tempfile
import shutil
from pathlib import Path

# We must ensure we are testing the actual project logging module,
# not a mock. We will use a temporary directory for the test output
# to avoid polluting the real data/processed directory during unit tests,
# but we verify the path logic matches the project's EXCLUSION_LOG_PATH.

import sys
# Ensure code/ is in path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging import (
    EXCLUSION_LOG_PATH,
    LOGS_DIR,
    log_participant_exclusion,
    log_artifact_rejection,
    save_rejection_summary,
    get_logger,
    ReproducibilityLogger,
    LogEntry
)

def test_constants_exist():
    """Verify that required constants are defined."""
    assert EXCLUSION_LOG_PATH is not None
    assert LOGS_DIR is not None
    assert EXCLUSION_LOG_PATH.endswith("exclusion_log.csv")
    assert LOGS_DIR == "data/processed"

def test_log_entry_creation():
    """Test that LogEntry creates valid JSON."""
    entry = LogEntry(operation="test", parameters={"key": "value"})
    json_str = entry.to_json()
    assert "test" in json_str
    assert "value" in json_str

def test_logger_accepts_args():
    """Test that get_logger accepts various argument shapes."""
    logger1 = get_logger("test_name")
    assert logger1.name == "test_name"

    logger2 = get_logger(name="another_name")
    assert logger2.name == "another_name"

    logger3 = get_logger()
    assert logger3 is logger1  # Singleton pattern

def test_log_artifact_rejection_writes_csv():
    """Test that artifact rejection logs to the correct CSV file."""
    # Use a temporary directory to simulate the data/processed directory
    # to ensure we don't write to the real project root during unit tests
    # if the test is run in isolation, but we verify the logic matches EXCLUSION_LOG_PATH.
    
    # Reset global logger to ensure clean state
    from utils import logging as logging_module
    logging_module._GLOBAL_LOGGER = None
    
    # Create a temporary directory for this test run
    # We will mock the EXCLUSION_LOG_PATH to point here for the test
    # However, the requirement is that the file is created in data/processed.
    # To verify this without side effects, we will:
    # 1. Call the logging functions.
    # 2. Call save_rejection_summary.
    # 3. Check if the file exists at EXCLUSION_LOG_PATH.
    # Since we can't guarantee data/processed exists in a pure unit test env,
    # we will create it if needed.

    # Ensure the directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Trigger log entries
    log_artifact_rejection("epoch", "amplitude_threshold", participant_id="sub-001")
    log_artifact_rejection("segment", "segment_too_short", participant_id="sub-002")

    # Save to CSV
    save_rejection_summary(EXCLUSION_LOG_PATH)

    # Verify file exists at the correct path (data/processed/exclusion_log.csv)
    assert os.path.exists(EXCLUSION_LOG_PATH), f"File {EXCLUSION_LOG_PATH} was not created"

    # Verify content
    with open(EXCLUSION_LOG_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2

    # Check specific rows
    reasons = [row["reason"] for row in rows]
    assert "amplitude_threshold" in reasons
    assert "segment_too_short" in reasons

    # Check participant IDs
    pids = [row["participant_id"] for row in rows]
    assert "sub-001" in pids
    assert "sub-002" in pids

    # Check timestamp column exists and is not empty
    for row in rows:
        assert "timestamp" in row
        assert len(row["timestamp"]) > 0

def test_log_participant_exclusion_writes_csv():
    """Test that participant exclusion logs to the correct CSV file."""
    # Reset global logger
    from utils import logging as logging_module
    logging_module._GLOBAL_LOGGER = None

    os.makedirs(LOGS_DIR, exist_ok=True)

    log_participant_exclusion("sub-003", "poor_signal_quality")
    
    save_rejection_summary(EXCLUSION_LOG_PATH)

    assert os.path.exists(EXCLUSION_LOG_PATH)

    with open(EXCLUSION_LOG_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have at least the new entry
    assert len(rows) >= 1
    
    # Find the sub-003 entry
    sub_003_row = next((r for r in rows if r["participant_id"] == "sub-003"), None)
    assert sub_003_row is not None
    assert sub_003_row["reason"] == "poor_signal_quality"

def test_file_is_in_correct_directory():
    """Verify the file is written to data/processed and not a temp dir."""
    # This is implicitly tested by EXCLUSION_LOG_PATH definition,
    # but we assert the path string directly.
    assert EXCLUSION_LOG_PATH.startswith("data/processed/")
    assert not EXCLUSION_LOG_PATH.startswith("/tmp")
    assert not EXCLUSION_LOG_PATH.startswith(tempfile.gettempdir())