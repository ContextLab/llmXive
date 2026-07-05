"""
Unit tests for logging infrastructure in code/utils.py.
Verifies that timestamp and task ID tracking work correctly (FR-007).
"""
import logging
import io
import sys
import re
import pytest
from datetime import datetime

# Import the module under test
from utils import setup_logging, set_task_id, get_task_id, get_logger, TaskIdFilter

def test_setup_logging_creates_handler():
    """Verify setup_logging creates a console handler and returns a logger."""
    logger = setup_logging()
    assert logger is not None
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_set_task_id_updates_global():
    """Verify set_task_id updates the internal global state."""
    set_task_id("T004")
    assert get_task_id() == "T004"
    
    set_task_id("T999")
    assert get_task_id() == "T999"

def test_task_id_injected_into_log_record():
    """Verify that log records contain the current task ID."""
    # Reset logger to ensure clean state for test
    logger = logging.getLogger("llmXive")
    logger.handlers.clear()
    set_task_id("TEST-TASK")
    
    logger = setup_logging(level=logging.INFO)
    
    # Capture log output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    
    # Re-apply the filter to the new handler
    handler.addFilter(TaskIdFilter())
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(task_id)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    logger.info("Test message")
    
    output = stream.getvalue()
    assert "[TEST-TASK]" in output
    assert "Test message" in output

def test_default_task_id_when_unset():
    """Verify that log records show 'N/A' if no task ID is set."""
    logger = logging.getLogger("llmXive")
    logger.handlers.clear()
    set_task_id(None) # Explicitly clear
    
    logger = setup_logging(level=logging.INFO)
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    handler.addFilter(TaskIdFilter())
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(task_id)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    logger.info("Message with no task ID")
    
    output = stream.getvalue()
    assert "[N/A]" in output
    assert "Message with no task ID" in output

def test_timestamp_format_in_log():
    """Verify that logs include a valid timestamp."""
    logger = logging.getLogger("llmXive")
    logger.handlers.clear()
    set_task_id("TS-TEST")
    
    logger = setup_logging(level=logging.INFO)
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    handler.addFilter(TaskIdFilter())
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(task_id)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    logger.info("Timestamp check")
    
    output = stream.getvalue()
    # Regex for YYYY-MM-DD HH:MM:SS
    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    assert re.search(timestamp_pattern, output) is not None