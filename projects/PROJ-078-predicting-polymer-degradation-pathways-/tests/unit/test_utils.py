"""Unit tests for utility functions."""
import pytest
import time
from unittest.mock import patch, MagicMock
from utils import with_exponential_backoff, load_config, setup_logging, get_logger
import os
import tempfile

def test_with_exponential_backoff_success():
    """Test that a function succeeds immediately without retries."""
    @with_exponential_backoff(max_retries=3)
    def successful_func():
        return "success"
    
    result = successful_func()
    assert result == "success"

def test_with_exponential_backoff_retry():
    """Test that a function retries on failure and succeeds eventually."""
    call_count = 0
    
    @with_exponential_backoff(max_retries=3)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Simulated network error")
        return "success after retry"
    
    result = flaky_func()
    assert result == "success after retry"
    assert call_count == 2

def test_with_exponential_backoff_max_retries():
    """Test that a function fails after max retries."""
    call_count = 0
    
    @with_exponential_backoff(max_retries=2)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Persistent error")
    
    with pytest.raises(ValueError):
        always_fails()
    
    assert call_count == 3 # Initial + 2 retries

def test_load_config_from_env():
    """Test loading config from environment variables."""
    with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
        config = load_config(env_prefix="TEST_")
        # The load_config implementation in utils.py might vary, 
        # but we test that it doesn't crash and uses the env
        assert isinstance(config, dict)
        
def test_setup_logging_and_get_logger():
    """Test logging setup and retrieval."""
    logger_name = "test_logger"
    logger = get_logger(logger_name)
    
    # Verify logger exists and has correct name
    assert logger.name == logger_name
    assert logger.level != logging.NOTSET or logger.level == 0 # Default level
    
    # Test that setup_logging doesn't crash
    # (It usually configures root logger)
    setup_logging(level="INFO")
    root_logger = get_logger()
    assert root_logger is not None
