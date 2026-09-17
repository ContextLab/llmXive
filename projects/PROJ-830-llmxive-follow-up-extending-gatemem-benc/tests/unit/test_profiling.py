"""
Unit tests for the profiling module.

These tests verify that the profiling utilities work correctly
and return standardized output keys as required by the task.
"""

import pytest
import time
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.profiling import (
    profile_execution,
    ProfileResult,
    get_process_memory_mb,
    get_peak_memory_mb,
    ProfileContext,
    start_profiling,
    stop_profiling,
    reset_profiling,
    profile_block,
    get_results_summary,
    save_results_to_file
)

def test_profile_execution_returns_dict():
    """Test that profile_execution returns a dictionary with standardized keys."""
    
    def dummy_function():
        time.sleep(0.01)
        return "success"
    
    result = profile_execution(dummy_function)
    
    # Verify return type
    assert isinstance(result, dict), "profile_execution must return a dictionary"
    
    # Verify required keys exist
    assert 'latency_ms' in result, "Result must contain 'latency_ms' key"
    assert 'peak_ram_mb' in result, "Result must contain 'peak_ram_mb' key"
    
    # Verify types
    assert isinstance(result['latency_ms'], float), "latency_ms must be a float"
    assert isinstance(result['peak_ram_mb'], float), "peak_ram_mb must be a float"
    
    # Verify values are non-negative
    assert result['latency_ms'] >= 0, "latency_ms must be non-negative"
    assert result['peak_ram_mb'] >= 0, "peak_ram_mb must be non-negative"
    
    # Verify latency is reasonable (should be > 0 for a sleep call)
    assert result['latency_ms'] > 0, "latency_ms should be > 0 for a function with sleep"

def test_profile_execution_latency_accuracy():
    """Test that profile_execution measures latency accurately."""
    
    def sleep_function():
        time.sleep(0.05)  # Sleep for 50ms
        return "done"
    
    result = profile_execution(sleep_function)
    
    # Latency should be at least 50ms (with some tolerance for overhead)
    assert result['latency_ms'] >= 45, f"Latency should be at least 45ms, got {result['latency_ms']}ms"

def test_profile_context_manager():
    """Test the ProfileContext context manager."""
    
    with ProfileContext() as ctx:
        time.sleep(0.02)
        result = ctx.get_result()
    
    assert isinstance(result, ProfileResult)
    assert result.latency_ms > 0
    assert result.peak_ram_mb >= 0

def test_get_process_memory_mb():
    """Test that get_process_memory_mb returns a valid float."""
    memory = get_process_memory_mb()
    assert isinstance(memory, float)
    assert memory >= 0

def test_get_peak_memory_mb():
    """Test that get_peak_memory_mb returns a valid float."""
    memory = get_peak_memory_mb()
    assert isinstance(memory, float)
    assert memory >= 0

def test_profile_block_decorator():
    """Test the profile_block decorator."""
    
    @profile_block("test_block")
    def decorated_function():
        time.sleep(0.01)
        return "result"
    
    result, profile_result = decorated_function()
    
    assert result == "result"
    assert isinstance(profile_result, ProfileResult)
    assert profile_result.latency_ms >= 0
    assert profile_result.peak_ram_mb >= 0

def test_get_results_summary():
    """Test the get_results_summary function."""
    
    results = [
        {'latency_ms': 10.0, 'peak_ram_mb': 100.0},
        {'latency_ms': 20.0, 'peak_ram_mb': 150.0},
        {'latency_ms': 30.0, 'peak_ram_mb': 200.0}
    ]
    
    summary = get_results_summary(results)
    
    assert 'mean_latency_ms' in summary
    assert 'std_latency_ms' in summary
    assert 'mean_peak_ram_mb' in summary
    assert 'std_peak_ram_mb' in summary
    
    # Verify calculated values
    assert summary['mean_latency_ms'] == 20.0
    assert summary['mean_peak_ram_mb'] == 150.0

def test_save_results_to_file(tmp_path):
    """Test saving results to a file."""
    
    results = {
        'latency_ms': 10.0,
        'peak_ram_mb': 100.0
    }
    
    filepath = tmp_path / "test_results.json"
    save_results_to_file(results, str(filepath))
    
    assert filepath.exists()
    
    import json
    with open(filepath, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == results