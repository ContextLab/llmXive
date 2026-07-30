"""
Unit tests for utility functions.
"""
import pytest
import logging
from utils import setup_logging, get_logger, retry_with_backoff
import time

def test_setup_logging_creates_handler(tmp_path):
    """Test that setup_logging creates a file handler."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_file, level=logging.INFO)
    
    assert logger is not None
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

def test_get_logger_returns_existing():
    """Test that get_logger returns the same logger instance."""
    logger1 = get_logger("test_logger")
    logger2 = get_logger("test_logger")
    assert logger1 is logger2

def test_retry_with_backoff_success():
    """Test retry_with_backoff on successful call."""
    call_count = 0
    
    @retry_with_backoff(max_retries=3)
    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = success_func()
    assert result == "success"
    assert call_count == 1

def test_retry_with_backoff_failure():
    """Test retry_with_backoff raises after max retries."""
    call_count = 0
    
    @retry_with_backoff(max_retries=2, backoff_factor=0.01)
    def fail_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        fail_func()
    
    assert call_count == 3  # Initial + 2 retries
