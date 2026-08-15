"""
Unit tests for the logging infrastructure.
"""
import pytest
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Import the module under test
from code.utils.logger import (
    setup_logger,
    track_error,
    get_tracked_errors,
    log_error,
    log_critical,
    log_exception,
    log_pipeline_step,
    get_log_file_path,
    get_error_summary,
    ERROR_CODES
)

# Test fixtures
@pytest.fixture(autouse=True)
def reset_error_tracker():
    """Reset error tracker before each test."""
    # Access internal state via the module
    import code.utils.logger as logger_module
    logger_module._error_tracker.clear()
    logger_module._save_error_tracker()
    yield
    logger_module._error_tracker.clear()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

def test_error_codes_registered():
    """Test that standard error codes are registered."""
    assert 101 in ERROR_CODES
    assert 102 in ERROR_CODES
    assert ERROR_CODES[101] == "Insufficient replicates (<3)"
    assert ERROR_CODES[102] == "Excessive replicates (>5)"

def test_track_error_basic():
    """Test basic error tracking functionality."""
    track_error(101, "Test error message")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 101
    assert errors[0]["message"] == "Test error message"
    assert "timestamp" in errors[0]
    assert errors[0]["error_name"] == ERROR_CODES[101]

def test_track_error_with_exception():
    """Test error tracking with exception."""
    try:
        raise ValueError("Test exception")
    except Exception as e:
        track_error(101, "Error with exception", e)
    
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["traceback"] is not None
    assert "ValueError" in errors[0]["traceback"]

def test_get_tracked_errors_returns_copy():
    """Test that get_tracked_errors returns a copy."""
    track_error(101, "Test")
    errors1 = get_tracked_errors()
    errors1.append({"fake": "error"})
    errors2 = get_tracked_errors()
    assert len(errors2) == 1  # Original should be unchanged

def test_log_error_tracks_and_logs():
    """Test that log_error both tracks and logs."""
    # This would normally be captured in a log capture fixture
    # For now, we verify tracking side-effect
    log_error(102, "Test log error")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 102

def test_log_critical_tracks():
    """Test that log_critical tracks errors."""
    log_critical("Critical system failure")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 999

def test_log_exception_tracks():
    """Test that log_exception tracks errors."""
    try:
        raise RuntimeError("Test runtime error")
    except Exception as e:
        log_exception(e, "Runtime error occurred")
    
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 999
    assert errors[0]["traceback"] is not None

def test_log_pipeline_step():
    """Test pipeline step logging."""
    log_pipeline_step("download", "STARTED")
    log_pipeline_step("download", "COMPLETED", {"files": 10})
    log_pipeline_step("align", "FAILED")
    
    # Just verify no exceptions are raised
    assert True

def test_unknown_error_code():
    """Test handling of unknown error codes."""
    # Should not crash, just warn
    track_error(9999, "Unknown error code test")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_name"] == "Unknown"

def test_get_error_summary_empty():
    """Test error summary when no errors."""
    summary = get_error_summary()
    assert "No errors tracked" in summary

def test_get_error_summary_with_errors():
    """Test error summary with tracked errors."""
    track_error(101, "Error 1")
    track_error(102, "Error 2")
    summary = get_error_summary()
    assert "2 total" in summary
    assert "101" in summary
    assert "102" in summary

def test_log_file_path_exists():
    """Test that log file path is valid."""
    log_path = get_log_file_path()
    assert isinstance(log_path, Path)
    assert log_path.name == "pipeline.log"

def test_multiple_errors_accumulate():
    """Test that multiple errors accumulate correctly."""
    for i in range(5):
        track_error(101, f"Error {i}")
    errors = get_tracked_errors()
    assert len(errors) == 5

def test_error_tracker_persistence(tmp_path):
    """Test that error tracker is persisted to disk."""
    # Change the module's error tracker file path for testing
    import code.utils.logger as logger_module
    original_tracker_file = logger_module.ERROR_TRACKER_FILE
    logger_module.ERROR_TRACKER_FILE = "test_tracker.json"
    logger_module.LOG_DIR = tmp_path / "logs"
    logger_module.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        track_error(101, "Persistence test")
        tracker_path = tmp_path / "logs" / "test_tracker.json"
        assert tracker_path.exists()
        
        with open(tracker_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["error_code"] == 101
    finally:
        logger_module.ERROR_TRACKER_FILE = original_tracker_file
        logger_module.LOG_DIR = Path("data/logs")

def test_log_pipeline_step_with_details():
    """Test pipeline step logging with details dictionary."""
    details = {"duration": 120, "files_processed": 5}
    log_pipeline_step("quantify", "COMPLETED", details)
    # Verify no exceptions
    assert True

def test_error_code_101_102_specific():
    """Test specific error codes for US1 validation."""
    track_error(101, "Too few replicates")
    track_error(102, "Too many replicates")
    errors = get_tracked_errors()
    assert errors[0]["error_name"] == ERROR_CODES[101]
    assert errors[1]["error_name"] == ERROR_CODES[102]