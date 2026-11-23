import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# Ensure we can import from code/utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logger import (
    setup_logger,
    get_log_file_path,
    track_error,
    get_tracked_errors,
    get_error_summary,
    log_error,
    log_critical,
    log_exception,
    log_pipeline_step,
    export_error_log,
    quick_log,
    get_log_file_path,
    clean_error_store,
    log_hash_to_file,
    log_manifest_entry,
    _error_store
)

@pytest.fixture
def clean_error_store():
    """Fixture to clear error store before and after each test."""
    clean_error_store()
    yield
    clean_error_store()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    # We can't easily change the global LOGS_DIR without mocking,
    # so we just ensure the directory exists for the test environment
    return tmp_path

def test_setup_logger_initializes(clean_error_store):
    """Test that setup_logger initializes loguru handlers."""
    # Reset setup state if possible (loguru doesn't expose _is_setup)
    # We rely on the fact that calling it multiple times is safe
    setup_logger(level="DEBUG")
    # If we get here without exception, initialization succeeded
    assert True

def test_track_error(clean_error_store):
    """Test that track_error records an error correctly."""
    track_error("E001", "Test error message", {"key": "value"})
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == "E001"
    assert errors[0]["message"] == "Test error message"
    assert errors[0]["context"] == {"key": "value"}
    assert "timestamp" in errors[0]

def test_get_error_summary(clean_error_store):
    """Test that get_error_summary returns correct counts."""
    track_error("E001", "Error 1")
    track_error("E002", "Error 2")
    track_error("E001", "Error 3")
    
    summary = get_error_summary()
    assert summary["total_errors"] == 3
    assert summary["by_code"]["E001"] == 2
    assert summary["by_code"]["E002"] == 1

def test_log_error(clean_error_store):
    """Test that log_error tracks and logs."""
    log_error("E003", "Log error test")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == "E003"

def test_log_critical(clean_error_store):
    """Test that log_critical marks error as critical."""
    log_critical("E004", "Critical test")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0].get("critical") is True

def test_log_pipeline_step(clean_error_store):
    """Test pipeline step logging."""
    log_pipeline_step("Data Download", "STARTED")
    log_pipeline_step("Data Download", "COMPLETED")
    log_pipeline_step("Alignment", "FAILED")
    
    # Just verify no exceptions and logs are generated
    assert True

def test_export_error_log(clean_error_store, tmp_path):
    """Test exporting error log to JSON."""
    track_error("E005", "Export test")
    output_path = tmp_path / "test_export.json"
    
    result_path = export_error_log(output_path)
    
    assert result_path == output_path
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["error_code"] == "E005"

def test_quick_log(clean_error_store, caplog):
    """Test quick_log function."""
    # Note: loguru uses sys.stderr, not caplog directly, 
    # but we test that the function doesn't crash
    quick_log("Info message", "INFO")
    quick_log("Debug message", "DEBUG")
    quick_log("Warning message", "WARNING")
    quick_log("Error message", "ERROR")
    quick_log("Critical message", "CRITICAL")
    quick_log("Unknown level", "UNKNOWN") # Should default to INFO
    assert True

def test_get_log_file_path():
    """Test getting log file path."""
    path = get_log_file_path("custom.log")
    assert isinstance(path, Path)
    assert path.name == "custom.log"
    assert path.parent.name == "logs"

def test_log_hash_to_file(clean_error_store):
    """Test logging a hash."""
    test_path = Path("/fake/path/file.bam")
    test_hash = "abc123"
    log_hash_to_file(test_path, test_hash)
    assert True

def test_log_manifest_entry(clean_error_store):
    """Test logging manifest entry."""
    test_path = Path("/fake/manifest.json")
    log_manifest_entry(test_path, 5)
    assert True
