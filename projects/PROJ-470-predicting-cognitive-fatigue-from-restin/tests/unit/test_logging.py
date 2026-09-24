"""Unit tests for the logging infrastructure (T006)."""
import os
import csv
import json
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure we can import code/utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging import (
    get_logger,
    log_participant_exclusion,
    log_artifact_rejection,
    save_rejection_summary,
    get_rejection_counts,
    LogEntry,
    ReproducibilityLogger
)


def test_exclusion_log_file_creation():
    """Test that exclusion_log.csv is created in data/processed/ with correct columns."""
    # Reset logger state for a clean test
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None

    # Ensure the target directory exists
    target_dir = Path("data/processed")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing file if present to test creation from scratch
    log_file = target_dir / "exclusion_log.csv"
    if log_file.exists():
        log_file.unlink()

    # Trigger a log entry
    log_participant_exclusion("sub-001", "artifact_contamination")

    # Assert file exists in the correct location
    assert log_file.exists(), f"exclusion_log.csv was not created at {log_file}"
    assert str(target_dir) in str(log_file), "File must be in data/processed/, not a temp dir"

    # Verify CSV structure
    with open(log_file, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) >= 1, "CSV must have at least a header row"
    header = rows[0]
    expected_columns = ["participant_id", "reason", "timestamp"]
    assert header == expected_columns, f"Header mismatch: got {header}, expected {expected_columns}"

    assert len(rows) >= 2, "CSV must have at least one data row after logging"
    data_row = rows[1]
    assert data_row[0] == "sub-001", f"Participant ID mismatch: got {data_row[0]}"
    assert data_row[1] == "artifact_contamination", f"Reason mismatch: got {data_row[1]}"
    assert len(data_row[2]) > 0, "Timestamp must not be empty"

def test_artifact_rejection_logging():
    """Test that artifact rejections are logged correctly."""
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None

    target_dir = Path("data/processed")
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "exclusion_log.csv"
    if log_file.exists():
        log_file.unlink()

    log_artifact_rejection("epoch", "epoch_123", "amplitude_threshold")

    assert log_file.exists()
    with open(log_file, "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Find the row with our artifact ID
    found = False
    for row in rows[1:]:  # Skip header
        if row[0] == "epoch_123" and row[1] == "amplitude_threshold":
            found = True
            break
    assert found, "Artifact rejection entry not found in CSV"

def test_get_rejection_counts():
    """Test that rejection counts are calculated correctly."""
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None

    log_participant_exclusion("sub-001", "bad_data")
    log_participant_exclusion("sub-002", "bad_data")
    log_artifact_rejection("epoch", "e1", "noise")

    counts = get_rejection_counts()
    assert counts.get("bad_data", 0) == 2
    assert counts.get("noise", 0) == 1

def test_logger_tolerance():
    """Test that the logger accepts various call shapes without raising."""
    logger = ReproducibilityLogger()
    
    # Standard log
    entry = logger.log("test_op", param1="value1")
    assert isinstance(entry, LogEntry)
    
    # Info/debug (should not raise)
    logger.info("test message")
    logger.debug("debug message")
    logger.warning("warning message")
    
    # Call with no args
    entry2 = logger.log()
    assert entry2.operation == ""

def test_save_rejection_summary_direct():
    """Test save_rejection_summary writes correctly when called directly."""
    import utils.logging
    utils.logging._GLOBAL_LOGGER = None

    target_dir = Path("data/processed")
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "exclusion_log.csv"
    if log_file.exists():
        log_file.unlink()

    # Log manually via entries
    logger = get_logger()
    logger.log("participant_exclusion", participant_id="sub-999", reason="manual_test")
    save_rejection_summary()

    assert log_file.exists()
    with open(log_file, "r") as f:
        content = f.read()
    
    assert "sub-999" in content
    assert "manual_test" in content
    assert "participant_id,reason,timestamp" in content