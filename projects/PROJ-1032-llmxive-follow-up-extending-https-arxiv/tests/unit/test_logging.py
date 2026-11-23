"""
Unit tests for src/utils/logging.py
"""
import json
import os
import logging
import tempfile
import shutil
import pytest

# We need to mock the LOG_OUTPUT_DIR to use a temp directory for testing
# so we don't pollute the real data/processed directory during tests.
import src.utils.logging as logging_module

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files during testing."""
    temp_dir = tempfile.mkdtemp()
    original_dir = logging_module.LOG_OUTPUT_DIR
    logging_module.LOG_OUTPUT_DIR = temp_dir
    yield temp_dir
    logging_module.LOG_OUTPUT_DIR = original_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_logger_creation(temp_log_dir):
    """Test that a logger is created successfully."""
    logger = logging_module.get_logger("test_logger", log_file="test_creation.json")
    assert logger is not None
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2  # File and Console

def test_json_formatting(temp_log_dir):
    """Test that log messages are formatted as valid JSON."""
    logger = logging_module.get_logger("test_json", log_file="test_format.json")
    
    # Log a message
    logger.info("Test message")
    
    # Read the file
    log_path = os.path.join(temp_log_dir, "test_format.json")
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        line = f.readline().strip()
        data = json.loads(line)
        
        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert "logger" in data

def test_log_metric_helper(temp_log_dir):
    """Test the log_metric helper function."""
    logger = logging_module.get_logger("test_metric", log_file="test_metric.json")
    
    logging_module.log_metric(logger, "accuracy", 0.95, step=100, model="phi-2")
    
    log_path = os.path.join(temp_log_dir, "test_metric.json")
    with open(log_path, 'r') as f:
        line = f.readline().strip()
        data = json.loads(line)
        
        assert data["data"]["metric_name"] == "accuracy"
        assert data["data"]["value"] == 0.95
        assert data["data"]["step"] == 100
        assert data["data"]["model"] == "phi-2"

def test_log_event_helper(temp_log_dir):
    """Test the log_event helper function."""
    logger = logging_module.get_logger("test_event", log_file="test_event.json")
    
    logging_module.log_event(logger, "START_TRAINING", "Starting training run", staleness=2)
    
    log_path = os.path.join(temp_log_dir, "test_event.json")
    with open(log_path, 'r') as f:
        line = f.readline().strip()
        data = json.loads(line)
        
        assert data["data"]["event_type"] == "START_TRAINING"
        assert data["message"].startswith("Event: START_TRAINING")
        assert data["data"]["staleness"] == 2

def test_multiple_handlers_not_added(temp_log_dir):
    """Test that calling get_logger multiple times doesn't duplicate handlers."""
    logger1 = logging_module.get_logger("test_dup", log_file="test_dup.json")
    initial_count = len(logger1.handlers)
    
    logger2 = logging_module.get_logger("test_dup", log_file="test_dup2.json")
    
    # Should be the same logger instance with same handlers
    assert len(logger2.handlers) == initial_count
    assert logger1 is logger2

def test_exception_logging(temp_log_dir):
    """Test that exceptions are logged correctly."""
    logger = logging_module.get_logger("test_exc", log_file="test_exc.json")
    
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Division failed")
    
    log_path = os.path.join(temp_log_dir, "test_exc.json")
    with open(log_path, 'r') as f:
        line = f.readline().strip()
        data = json.loads(line)
        
        assert "exception" in data
        assert "ZeroDivisionError" in data["exception"]