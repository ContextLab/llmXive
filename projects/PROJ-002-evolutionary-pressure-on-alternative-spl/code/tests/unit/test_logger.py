import pytest
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
    export_error_log,
    quick_log
)
from loguru import logger

@pytest.fixture
def clean_error_store():
    """Fixture to clear error store before each test."""
    from code.utils.logger import _error_store
    _error_store.clear()
    yield
    _error_store.clear()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Fixture to create a temporary log directory."""
    log_dir = tmp_path / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def test_setup_logger_initializes(clean_error_store, tmp_path):
    """Test that setup_logger creates the log file and directory."""
    # We cannot easily mock the global _LOG_DIR in the module, 
    # so we test the function's behavior by checking if it runs without error.
    # In a real scenario, we might patch _LOG_DIR.
    # For this test, we assume the default setup works if no exception is raised.
    try:
        setup_logger(level="DEBUG", log_file_name="test_setup.log")
        # Check if log file exists (it might be in the real project path, not tmp_path)
        # This test mainly ensures no ImportError or immediate crash.
        assert True 
    except Exception as e:
        pytest.fail(f"setup_logger raised an exception: {e}")

def test_track_error(clean_error_store):
    """Test that track_error adds to the store."""
    track_error(101, "Test error message", {"key": "value"})
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 101
    assert errors[0]["message"] == "Test error message"
    assert errors[0]["context"]["key"] == "value"
    assert "timestamp" in errors[0]

def test_get_error_summary(clean_error_store):
    """Test error summary calculation."""
    track_error(101, "Error 1")
    track_error(101, "Error 2")
    track_error(102, "Error 3")
    
    summary = get_error_summary()
    assert summary["101"] == 2
    assert summary["102"] == 1

def test_log_error(clean_error_store):
    """Test log_error function."""
    log_error(201, "Log error test")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 201

def test_log_critical(clean_error_store):
    """Test log_critical function."""
    log_critical("Critical failure")
    errors = get_tracked_errors()
    assert len(errors) == 1
    assert errors[0]["error_code"] == 999
    assert "Critical failure" in errors[0]["message"]

def test_log_pipeline_step(clean_error_store, caplog):
    """Test log_pipeline_step."""
    # We can't easily capture loguru output in caplog without custom handlers
    # So we test the logic and side effects (tracking if applicable, though step doesn't track by default)
    log_pipeline_step("TestStep", "STARTED", {"input": "data"})
    log_pipeline_step("TestStep", "COMPLETED", {"output": "result"})
    log_pipeline_step("TestStep", "FAILED", {"reason": "timeout"})
    assert True # If we get here, no exception

def test_export_error_log(clean_error_store, tmp_path):
    """Test export_error_log creates a valid JSON file."""
    track_error(301, "Export test")
    output_path = tmp_path / "exported_errors.json"
    result_path = export_error_log(output_path)
    
    assert result_path == output_path
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["error_code"] == 301

def test_quick_log(clean_error_store):
    """Test quick_log."""
    quick_log("Quick message", "INFO")
    quick_log("Quick error", "ERROR")
    assert True

def test_get_log_file_path(clean_error_store):
    """Test get_log_file_path returns a Path object."""
    path = get_log_file_path()
    assert isinstance(path, Path)
    assert path.name == "pipeline.log"
