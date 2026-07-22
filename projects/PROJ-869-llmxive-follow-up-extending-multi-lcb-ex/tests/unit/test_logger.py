"""
Unit tests for the logging utilities.
"""
import pytest
import logging
import json
import tempfile
from pathlib import Path
from code.utils.logger import get_logger, setup_logging, log_error_to_file, log_execution_failure

def test_get_logger_creates_instance():
    """Test that get_logger returns a valid logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"
    assert len(logger.handlers) > 0

def test_get_logger_reuses_instance():
    """Test that calling get_logger multiple times returns the same handler setup."""
    logger1 = get_logger("test_reuse")
    logger2 = get_logger("test_reuse")
    # Should have the same handlers (or at least not duplicate if called again)
    assert logger1 is logger2

def test_setup_logging_with_file(tmp_path):
    """Test setup_logging with a file handler."""
    log_file = tmp_path / "test.log"
    setup_logging(log_file=log_file, level=logging.DEBUG)
    
    assert log_file.exists()
    
    # Verify content by logging something
    logger = get_logger("test_setup")
    logger.info("Test message")
    
    # Re-open to check content (handlers might buffer)
    # Force flush by getting a new logger or closing handlers
    root = logging.getLogger()
    for handler in root.handlers:
        handler.flush()
    
    assert log_file.read_text().strip() != ""
    assert "Test message" in log_file.read_text()

def test_log_error_to_file_creates_json(tmp_path):
    """Test that log_error_to_file creates a valid JSON file."""
    error_file = tmp_path / "errors.json"
    error_details = {
        "task_id": "T007",
        "message": "Test error",
        "severity": "ERROR"
    }
    
    log_error_to_file(error_details, log_path=error_file)
    
    assert error_file.exists()
    with open(error_file, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["task_id"] == "T007"
    assert data[0]["message"] == "Test error"

def test_log_error_to_file_appends(tmp_path):
    """Test that log_error_to_file appends to existing log."""
    error_file = tmp_path / "errors.json"
    
    # First log
    log_error_to_file({"task_id": "T001", "message": "First"}, log_path=error_file)
    # Second log
    log_error_to_file({"task_id": "T002", "message": "Second"}, log_path=error_file)
    
    with open(error_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["task_id"] == "T001"
    assert data[1]["task_id"] == "T002"

def test_log_execution_failure(tmp_path):
    """Test log_execution_failure creates correct structure."""
    # Monkeypatch the config to use our temp file
    import code.utils.logger as logger_module
    original_path = logger_module.config.ERROR_LOG_PATH
    logger_module.config.ERROR_LOG_PATH = tmp_path / "pipeline_errors.json"
    
    try:
        log_execution_failure("T007", "Simulated failure", "Traceback: ...")
        
        log_path = tmp_path / "pipeline_errors.json"
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) > 0
        last_error = data[-1]
        assert last_error["task_id"] == "T007"
        assert last_error["error_type"] == "ExecutionFailure"
        assert last_error["traceback"] == "Traceback: ..."
    finally:
        logger_module.config.ERROR_LOG_PATH = original_path