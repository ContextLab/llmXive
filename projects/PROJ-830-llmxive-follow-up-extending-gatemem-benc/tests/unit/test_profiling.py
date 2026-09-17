"""
Unit tests for the profiling module.
"""

import pytest
import time
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.profiling import (
    profile_execution,
    get_process_memory_mb,
    get_peak_memory_mb,
    start_profiling,
    stop_profiling,
    reset_profiling,
    profile_block,
    profile_function,
    ProfileResult,
    get_results_summary,
    save_results_to_file
)


class TestProfileExecution:
    """Tests for the profile_execution function."""

    def test_profile_execution_returns_dict(self):
        """Test that profile_execution returns a dict with required keys."""
        
        def dummy_task():
            time.sleep(0.01)
            return "done"
        
        result = profile_execution(dummy_task)
        
        assert isinstance(result, dict), "Result must be a dictionary"
        assert 'latency_ms' in result, "Missing 'latency_ms' key"
        assert 'peak_ram_mb' in result, "Missing 'peak_ram_mb' key"
        assert isinstance(result['latency_ms'], float), "latency_ms must be float"
        assert isinstance(result['peak_ram_mb'], float), "peak_ram_mb must be float"
        assert result['latency_ms'] >= 0, "latency_ms must be non-negative"
        assert result['peak_ram_mb'] >= 0, "peak_ram_mb must be non-negative"

    def test_profile_execution_latency_positive(self):
        """Test that latency is positive for a task with sleep."""
        
        def slow_task():
            time.sleep(0.05)
            return "done"
        
        result = profile_execution(slow_task)
        
        assert result['latency_ms'] >= 50.0, f"Expected latency >= 50ms, got {result['latency_ms']}"

    def test_profile_execution_memory_allocation(self):
        """Test that memory profiling detects allocation."""
        
        def memory_task():
            # Allocate a list
            data = [i for i in range(100000)]
            return len(data)
        
        result = profile_execution(memory_task)
        
        # Memory should be positive
        assert result['peak_ram_mb'] > 0, "Expected positive memory usage"


class TestGetProcessMemoryMb:
    """Tests for get_process_memory_mb function."""

    def test_get_process_memory_mb_returns_float(self):
        """Test that get_process_memory_mb returns a float."""
        memory = get_process_memory_mb()
        assert isinstance(memory, float), "Must return float"
        assert memory >= 0, "Memory must be non-negative"


class TestGetPeakMemoryMb:
    """Tests for get_peak_memory_mb function."""

    def test_get_peak_memory_mb_returns_float(self):
        """Test that get_peak_memory_mb returns a float."""
        peak = get_peak_memory_mb()
        assert isinstance(peak, float), "Must return float"
        assert peak >= 0, "Peak memory must be non-negative"


class TestStartStopProfiling:
    """Tests for start_profiling and stop_profiling context managers."""

    def test_start_stop_profiling(self):
        """Test basic start/stop profiling workflow."""
        with start_profiling() as ctx:
            time.sleep(0.01)
            start_time = ctx['start_time']
        
        result = stop_profiling(start_time)
        
        assert 'latency_ms' in result
        assert 'peak_ram_mb' in result
        assert result['latency_ms'] >= 0
        assert result['peak_ram_mb'] >= 0


class TestProfileFunction:
    """Tests for the profile_function decorator."""

    def test_profile_function_decorator(self):
        """Test that profile_function decorator works correctly."""
        
        @profile_function
        def decorated_task():
            time.sleep(0.01)
            return "done"
        
        result = decorated_task()
        
        # The result should be the original return value
        assert result == "done"
        # But it should also have profiling attributes added (if dict) or logged


class TestProfileBlock:
    """Tests for the profile_block context manager."""

    def test_profile_block_context_manager(self):
        """Test that profile_block context manager works."""
        with profile_block("test_block") as ctx:
            time.sleep(0.01)
            assert 'label' in ctx
            assert ctx['label'] == "test_block"


class TestGetResultsSummary:
    """Tests for get_results_summary function."""

    def test_get_results_summary_with_data(self):
        """Test summary calculation with sample data."""
        results = [
            {'latency_ms': 10.0, 'peak_ram_mb': 100.0},
            {'latency_ms': 20.0, 'peak_ram_mb': 150.0},
            {'latency_ms': 30.0, 'peak_ram_mb': 200.0}
        ]
        
        summary = get_results_summary(results)
        
        assert 'latency_ms_mean' in summary
        assert 'latency_ms_std' in summary
        assert 'latency_ms_min' in summary
        assert 'latency_ms_max' in summary
        assert 'peak_ram_mb_mean' in summary
        assert 'peak_ram_mb_std' in summary
        assert 'peak_ram_mb_min' in summary
        assert 'peak_ram_mb_max' in summary
        
        assert summary['latency_ms_mean'] == 20.0
        assert summary['latency_ms_min'] == 10.0
        assert summary['latency_ms_max'] == 30.0

    def test_get_results_summary_empty_list(self):
        """Test summary calculation with empty list."""
        summary = get_results_summary([])
        
        assert summary['latency_ms_mean'] == 0.0
        assert summary['peak_ram_mb_mean'] == 0.0


class TestSaveResultsToFile:
    """Tests for save_results_to_file function."""

    def test_save_results_to_file(self, tmp_path):
        """Test saving results to a file."""
        results = {
            'latency_ms': 10.5,
            'peak_ram_mb': 123.4,
            'function_name': 'test_func'
        }
        
        output_path = tmp_path / "profiling_results.json"
        save_results_to_file(results, str(output_path))
        
        assert output_path.exists(), "Output file must exist"
        
        import json
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['latency_ms'] == 10.5
        assert loaded['peak_ram_mb'] == 123.4
        assert loaded['function_name'] == 'test_func'

def test_profile_context_manager():
    """Test the ProfileContext context manager."""
    
    with ProfileContext() as ctx:
        time.sleep(0.02)
        result = ctx.get_result()
    
    assert isinstance(result, ProfileResult)
    assert result.latency_ms > 0
    assert result.peak_ram_mb >= 0

class TestStandardizedKeys:
    """Tests to ensure standardized keys across all profiling functions."""

    def test_all_profiling_functions_use_standard_keys(self):
        """Verify that all profiling functions return standardized keys."""
        
        def dummy_task():
            return "done"
        
        # Test profile_execution
        result_exec = profile_execution(dummy_task)
        assert set(result_exec.keys()) == {'latency_ms', 'peak_ram_mb'}, \
            f"profile_execution keys mismatch: {result_exec.keys()}"
        
        # Test start/stop profiling
        with start_profiling() as ctx:
            time.sleep(0.01)
            start_time = ctx['start_time']
        
        result_stop = stop_profiling(start_time)
        assert set(result_stop.keys()) == {'latency_ms', 'peak_ram_mb'}, \
            f"stop_profiling keys mismatch: {result_stop.keys()}"