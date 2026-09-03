"""
Unit tests for the logging infrastructure (T006).

This test verifies that:
1. The exclusion log file is created in data/processed/exclusion_log.csv
2. The file contains the correct columns: participant_id, reason, timestamp
3. The logging functions can be called without errors
4. The file is created in the correct location (not a temporary directory)
"""
import os
import csv
import pytest
from pathlib import Path
from datetime import datetime
import shutil

# Import the logging module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from utils.logging import (
    get_logger,
    log_artifact_rejection,
    log_participant_exclusion,
    save_exclusion_log_csv,
    get_rejection_counts,
    EXCLUSION_LOG_PATH,
    LOGS_DIR
)


@pytest.fixture(autouse=True)
def cleanup_exclusion_log():
    """Clean up the exclusion log file before and after each test."""
    # Clean up before test
    if EXCLUSION_LOG_PATH.exists():
        EXCLUSION_LOG_PATH.unlink()
    
    yield
    
    # Clean up after test
    if EXCLUSION_LOG_PATH.exists():
        EXCLUSION_LOG_PATH.unlink()


def test_exclusion_log_file_location():
    """Test that the exclusion log is created in data/processed/, not a temp directory."""
    # Ensure the file path is in data/processed
    assert str(EXCLUSION_LOG_PATH).startswith("data/processed")
    assert EXCLUSION_LOG_PATH.name == "exclusion_log.csv"
    
    # Verify the directory exists
    assert LOGS_DIR.exists()
    assert LOGS_DIR.is_dir()


def test_log_artifact_rejection_creates_file():
    """Test that logging an artifact rejection creates the exclusion log file."""
    # Log an artifact rejection
    log_artifact_rejection("participant_001", "amplitude_threshold")
    
    # Verify the file was created
    assert EXCLUSION_LOG_PATH.exists(), "Exclusion log file was not created"
    assert EXCLUSION_LOG_PATH.is_file(), "Exclusion log path is not a file"


def test_log_artifact_rejection_has_correct_columns():
    """Test that the exclusion log has the correct columns."""
    # Log an artifact rejection
    log_artifact_rejection("participant_001", "amplitude_threshold")
    
    # Read the file and verify columns
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        expected_columns = ['participant_id', 'reason', 'timestamp']
        assert header == expected_columns, f"Expected columns {expected_columns}, got {header}"


def test_log_participant_exclusion():
    """Test that logging a participant exclusion works correctly."""
    # Log a participant exclusion
    log_participant_exclusion("participant_002", "segment_too_short")
    
    # Verify the file was created and contains the entry
    assert EXCLUSION_LOG_PATH.exists()
    
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        assert rows[0]['participant_id'] == "participant_002"
        assert rows[0]['reason'] == "segment_too_short"
        assert 'timestamp' in rows[0]
        assert rows[0]['timestamp'] != ""


def test_multiple_log_entries():
    """Test that multiple log entries are appended correctly."""
    # Log multiple events
    log_artifact_rejection("participant_001", "amplitude_threshold")
    log_participant_exclusion("participant_002", "segment_too_short")
    log_artifact_rejection("participant_003", "line_noise")
    
    # Verify all entries are present
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
        
        # Check each entry
        assert rows[0]['participant_id'] == "participant_001"
        assert rows[0]['reason'] == "amplitude_threshold"
        
        assert rows[1]['participant_id'] == "participant_002"
        assert rows[1]['reason'] == "segment_too_short"
        
        assert rows[2]['participant_id'] == "participant_003"
        assert rows[2]['reason'] == "line_noise"


def test_save_exclusion_log_csv():
    """Test the save_exclusion_log_csv function."""
    # Prepare test data
    test_data = [
        {'participant_id': 'participant_001', 'reason': 'amplitude_threshold', 'timestamp': '2024-01-01T12:00:00'},
        {'participant_id': 'participant_002', 'reason': 'segment_too_short', 'timestamp': '2024-01-01T12:01:00'}
    ]
    
    # Save the data
    save_exclusion_log_csv(test_data)
    
    # Verify the file was created and contains the data
    assert EXCLUSION_LOG_PATH.exists()
    
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        assert rows[0]['participant_id'] == 'participant_001'
        assert rows[1]['participant_id'] == 'participant_002'


def test_get_rejection_counts():
    """Test that get_rejection_counts returns correct counts."""
    # Log multiple events with different reasons
    log_artifact_rejection("participant_001", "amplitude_threshold")
    log_artifact_rejection("participant_002", "amplitude_threshold")
    log_participant_exclusion("participant_003", "segment_too_short")
    log_artifact_rejection("participant_004", "line_noise")
    
    # Get counts
    counts = get_rejection_counts()
    
    assert counts['amplitude_threshold'] == 2
    assert counts['segment_too_short'] == 1
    assert counts['line_noise'] == 1


def test_get_logger_returns_reproducible_logger():
    """Test that get_logger returns a ReproducibilityLogger instance."""
    logger = get_logger("test_logger")
    
    # Verify it's the correct type
    from utils.logging import ReproducibilityLogger
    assert isinstance(logger, ReproducibilityLogger)
    
    # Verify it has the expected methods
    assert hasattr(logger, 'log')
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'warning')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'critical')


def test_logger_handles_arbitrary_calls():
    """Test that the logger handles arbitrary call shapes without raising."""
    logger = get_logger("test_logger")
    
    # These should not raise any errors
    logger.log("operation", param1="value1", param2="value2")
    logger.info("info message")
    logger.debug("debug message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    logger.any_unknown_method("arg1", arg2="value")
    
    # Verify the logger didn't crash
    assert True


def test_log_entry_to_json():
    """Test that LogEntry can be converted to JSON."""
    from utils.logging import LogEntry
    
    entry = LogEntry(operation="test", parameters={"key": "value"})
    json_str = entry.to_json()
    
    import json
    parsed = json.loads(json_str)
    
    assert parsed['operation'] == "test"
    assert parsed['parameters']['key'] == "value"
    assert 'timestamp' in parsed


def test_file_not_in_temp_directory():
    """Verify the exclusion log is NOT in a temporary directory."""
    # Log an event to create the file
    log_artifact_rejection("participant_001", "test_reason")
    
    # Verify the file path is not in /tmp, /var/tmp, or similar
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    assert not str(EXCLUSION_LOG_PATH).startswith(temp_dir), \
        f"Exclusion log should not be in temp directory {temp_dir}"
    assert not str(EXCLUSION_LOG_PATH).startswith("/tmp"), \
        "Exclusion log should not be in /tmp"
    assert not str(EXCLUSION_LOG_PATH).startswith("/var/tmp"), \
        "Exclusion log should not be in /var/tmp"
    
    # Verify it IS in data/processed
    assert str(EXCLUSION_LOG_PATH).startswith("data/processed"), \
        f"Exclusion log should be in data/processed, got {EXCLUSION_LOG_PATH}"