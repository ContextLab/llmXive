"""
Tests for logging infrastructure.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.logging_config import (
    JSONLogHandler,
    setup_logging,
    log_mapping,
    get_project_logger
)

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_file = tmp_path / "test_log.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # Initialize with empty list
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump([], f)
    return log_file

def test_json_handler_creates_file(tmp_path):
    """Test that JSON handler creates log file if it doesn't exist."""
    log_file = tmp_path / "new_log.json"
    handler = JSONLogHandler(log_file)
    
    assert log_file.exists()
    with open(log_file, 'r') as f:
        content = json.load(f)
    assert content == []

def test_json_handler_appends_entries(temp_log_file):
    """Test that JSON handler correctly appends log entries."""
    handler = JSONLogHandler(temp_log_file)
    
    # Create a mock log record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    handler.emit(record)
    
    with open(temp_log_file, 'r') as f:
        logs = json.load(f)
    
    assert len(logs) == 1
    assert logs[0]['message'] == "Test message"
    assert logs[0]['level'] == "INFO"

def test_setup_logging_returns_logger(tmp_path):
    """Test that setup_logging returns a configured logger."""
    log_file = tmp_path / "setup_test.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, 'w') as f:
        json.dump([], f)
    
    logger = setup_logging(log_file=log_file)
    
    assert logger is not None
    assert logger.name == "social_exclusion"
    assert len(logger.handlers) == 2  # JSON handler + console handler

def test_log_mapping_function(temp_log_file):
    """Test that log_mapping correctly logs structured data."""
    logger = setup_logging(log_file=temp_log_file)
    
    log_mapping(
        logger,
        dataset_id="test_001",
        raw_condition="ignored",
        binary_condition=1,
        message="Test mapping"
    )
    
    with open(temp_log_file, 'r') as f:
        logs = json.load(f)
    
    assert len(logs) == 1
    assert logs[0]['dataset_id'] == "test_001"
    assert logs[0]['raw_condition'] == "ignored"
    assert logs[0]['binary_condition'] == 1
    assert logs[0]['message'] == "Test mapping"

def test_get_project_logger():
    """Test that get_project_logger returns a valid logger."""
    logger = get_project_logger()
    
    assert logger is not None
    assert logger.name == "social_exclusion"

# Import logging for the test
import logging
