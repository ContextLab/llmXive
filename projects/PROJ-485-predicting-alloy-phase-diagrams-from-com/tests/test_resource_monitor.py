import os
import json
import time
import pytest
from unittest.mock import patch, MagicMock

from utils.resource_monitor import (
    get_peak_memory_gb,
    check_resource_constraints,
    log_resource_usage,
    resource_monitor_wrapper,
    MAX_EXECUTION_TIME_SECONDS,
    MAX_MEMORY_GB
)
from utils.error_codes import ErrorCode

def test_get_peak_memory_gb():
    """Test that get_peak_memory_gb returns a positive float."""
    mem = get_peak_memory_gb()
    assert isinstance(mem, float)
    assert mem > 0

def test_check_resource_constraints_time():
    """Test that time violation is detected."""
    # Within limits
    assert not check_resource_constraints(100, 1.0)
    
    # Exceeds time limit
    assert check_resource_constraints(MAX_EXECUTION_TIME_SECONDS + 100, 1.0)

def test_check_resource_constraints_memory():
    """Test that memory violation is detected."""
    # Within limits
    assert not check_resource_constraints(100, 1.0)
    
    # Exceeds memory limit
    assert check_resource_constraints(100, MAX_MEMORY_GB + 1.0)

def test_log_resource_usage():
    """Test that log_resource_usage writes correct JSON."""
    temp_path = "data/artifacts/test_resource_log.json"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    
    log_resource_usage(temp_path, 120, 2.5)
    
    assert os.path.exists(temp_path)
    with open(temp_path, 'r') as f:
        data = json.load(f)
    
    assert data["execution_time_seconds"] == 120
    assert abs(data["peak_memory_gb"] - 2.5) < 0.001
    
    # Cleanup
    os.remove(temp_path)

def test_resource_monitor_wrapper_success():
    """Test that the wrapper logs resources and returns result on success."""
    temp_path = "data/artifacts/test_wrapper_log.json"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)

    @resource_monitor_wrapper
    def dummy_task(resource_log_path=temp_path):
        time.sleep(0.1)
        return "done"

    try:
        result = dummy_task()
        assert result == "done"
        
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            data = json.load(f)
        
        assert "execution_time_seconds" in data
        assert "peak_memory_gb" in data
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_resource_monitor_wrapper_time_limit():
    """Test that the wrapper raises RuntimeError if time limit exceeded."""
    # We mock time.time to simulate a long execution
    original_time = time.time
    call_count = [0]
    
    def mock_time():
        call_count[0] += 1
        if call_count[0] == 1:
            return 0.0
        else:
            return MAX_EXECUTION_TIME_SECONDS + 100.0 # Simulate huge duration

    @resource_monitor_wrapper
    def slow_task(resource_log_path="data/artifacts/test_slow_log.json"):
        return "done"

    os.makedirs("data/artifacts", exist_ok=True)

    with patch('time.time', side_effect=mock_time):
        with pytest.raises(RuntimeError) as exc_info:
            slow_task()
        
        assert ErrorCode.RESOURCE_LIMIT_EXCEEDED.value in str(exc_info.value)

    # Cleanup
    if os.path.exists("data/artifacts/test_slow_log.json"):
        os.remove("data/artifacts/test_slow_log.json")

def test_resource_monitor_wrapper_memory_limit():
    """Test that the wrapper raises RuntimeError if memory limit exceeded."""
    # We mock get_peak_memory_gb to simulate high memory
    with patch('utils.resource_monitor.get_peak_memory_gb', return_value=MAX_MEMORY_GB + 5.0):
        @resource_monitor_wrapper
        def memory_hog(resource_log_path="data/artifacts/test_mem_log.json"):
            return "done"
        
        os.makedirs("data/artifacts", exist_ok=True)
        
        with pytest.raises(RuntimeError) as exc_info:
            memory_hog()
        
        assert ErrorCode.RESOURCE_LIMIT_EXCEEDED.value in str(exc_info.value)

    # Cleanup
    if os.path.exists("data/artifacts/test_mem_log.json"):
        os.remove("data/artifacts/test_mem_log.json")