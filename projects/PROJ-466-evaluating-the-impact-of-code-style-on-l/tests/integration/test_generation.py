"""
Integration tests for the generation loop with timeout and memory probing.
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import pipeline components
from generation.generator import get_available_memory_gb, calculate_batch_size
from utils.timeout_decorator import timeout_decorator, TaskTimeoutError
from utils.logger import log_memory_usage, get_memory_log_path

def test_memory_probing():
    """Test that memory probing functions work."""
    mem_gb = get_available_memory_gb()
    assert mem_gb is not None
    assert mem_gb > 0

def test_batch_size_calculation():
    """Test batch size calculation based on memory."""
    # Mock available memory
    with patch('generation.generator.get_available_memory_gb', return_value=4.0):
        batch_size = calculate_batch_size()
        assert batch_size > 0

def test_timeout_decorator():
    """Test that the timeout decorator raises an error on timeout."""
    @timeout_decorator(1)
    def slow_function():
        time.sleep(2)
        return True

    with pytest.raises(TaskTimeoutError):
        slow_function()

def test_timeout_decorator_success():
    """Test that the timeout decorator allows fast functions."""
    @timeout_decorator(5)
    def fast_function():
        time.sleep(0.1)
        return True

    result = fast_function()
    assert result is True

def test_memory_logging():
    """Test that memory logging works."""
    log_path = get_memory_log_path()
    # Ensure the directory exists for the log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_memory_usage("test_key", 1.5)
    
    # Verify log file exists and contains entry
    assert log_path.exists()
    with open(log_path, 'r') as f:
        log_data = json.load(f)
        assert "test_key" in log_data or len(log_data) > 0
