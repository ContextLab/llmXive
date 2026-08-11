"""
Unit tests for the profiling module.

Tests verify that profiling functions return standardized results
and handle edge cases correctly.
"""

import pytest
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.profiling import (
    ProfileResult,
    get_process_memory_mb,
    get_peak_memory_mb,
    start_profiling,
    stop_profiling,
    reset_profiling,
    profile_block,
    profile_function,
    profile_execution,
    get_results_summary,
    save_results_to_file
)

class TestProfileResult:
    """Tests for ProfileResult named tuple."""

    def test_profile_result_creation(self):
        """Test that ProfileResult can be created with expected fields."""
        result = ProfileResult(latency_ms=100.5, peak_ram_mb=50.25)
        assert result.latency_ms == 100.5
        assert result.peak_ram_mb == 50.25
        assert isinstance(result.latency_ms, float)
        assert isinstance(result.peak_ram_mb, float)

class TestMemoryFunctions:
    """Tests for memory measurement functions."""

    def test_get_process_memory_mb_returns_float(self):
        """Test that get_process_memory_mb returns a float."""
        result = get_process_memory_mb()
        assert isinstance(result, float)
        assert result >= 0.0

    def test_get_peak_memory_mb_returns_float(self):
        """Test that get_peak_memory_mb returns a float."""
        result = get_peak_memory_mb()
        assert isinstance(result, float)
        assert result >= 0.0

class TestStartStopProfiling:
    """Tests for start/stop profiling functions."""

    def test_start_profiling_initializes(self):
        """Test that start_profiling initializes correctly."""
        start_profiling()
        # If we get here without error, initialization succeeded
        stop_profiling()

    def test_stop_profiling_returns_profile_result(self):
        """Test that stop_profiling returns a ProfileResult."""
        start_profiling()
        time.sleep(0.01)  # Small delay
        result = stop_profiling()
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 0.0
        assert result.peak_ram_mb >= 0.0

    def test_stop_profiling_without_start(self):
        """Test that stop_profiling handles being called without start."""
        # Ensure profiling is not active
        result = stop_profiling()
        assert isinstance(result, ProfileResult)
        assert result.latency_ms == 0.0
        assert result.peak_ram_mb == 0.0

    def test_reset_profiling(self):
        """Test that reset_profiling resets state."""
        start_profiling()
        time.sleep(0.01)
        reset_profiling()
        # Should be able to continue profiling after reset
        time.sleep(0.01)
        result = stop_profiling()
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 0.0

class TestProfileBlock:
    """Tests for profile_block context manager."""

    def test_profile_block_executes_code(self):
        """Test that profile_block executes the code inside it."""
        executed = False
        with profile_block("test"):
            executed = True
        assert executed

    def test_profile_block_returns_result(self):
        """Test that profile_block context yields a result."""
        with profile_block("test") as result:
            time.sleep(0.01)
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 0.0

class TestProfileFunction:
    """Tests for profile_function decorator."""

    def test_profile_function_preserves_function(self):
        """Test that profile_function decorator preserves function behavior."""
        @profile_function
        def dummy_func():
            return "success"
        
        result, profile_result = dummy_func()
        assert result == "success"
        assert isinstance(profile_result, ProfileResult)

    def test_profile_function_with_args(self):
        """Test that profile_function works with arguments."""
        @profile_function
        def add(a, b):
            return a + b
        
        result, profile_result = add(2, 3)
        assert result == 5
        assert isinstance(profile_result, ProfileResult)

class TestProfileExecution:
    """Tests for profile_execution decorator (main interface)."""

    def test_profile_execution_returns_dict(self):
        """Test that profile_execution returns a dict with standardized keys."""
        @profile_execution
        def dummy_func():
            time.sleep(0.01)
            return "result"
        
        result = dummy_func()
        assert isinstance(result, dict)
        assert 'latency_ms' in result
        assert 'peak_ram_mb' in result
        assert isinstance(result['latency_ms'], float)
        assert isinstance(result['peak_ram_mb'], float)

    def test_profile_execution_with_exception(self):
        """Test that profile_execution propagates exceptions."""
        @profile_execution
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_func()

    def test_profile_execution_keys_are_standardized(self):
        """Test that keys match the required standardized format."""
        @profile_execution
        def dummy_func():
            return None
        
        result = dummy_func()
        expected_keys = {'latency_ms', 'peak_ram_mb'}
        assert set(result.keys()) == expected_keys

class TestGetResultsSummary:
    """Tests for get_results_summary function."""

    def test_get_results_summary_with_data(self):
        """Test summary calculation with actual data."""
        results = [
            ProfileResult(100.0, 50.0),
            ProfileResult(200.0, 100.0),
            ProfileResult(150.0, 75.0)
        ]
        
        summary = get_results_summary(results)
        
        assert isinstance(summary, dict)
        assert 'mean_latency_ms' in summary
        assert 'std_latency_ms' in summary
        assert 'mean_peak_ram_mb' in summary
        assert 'std_peak_ram_mb' in summary
        
        # Verify calculations
        assert summary['mean_latency_ms'] == 150.0
        assert summary['mean_peak_ram_mb'] == 75.0

    def test_get_results_summary_empty_list(self):
        """Test summary calculation with empty list."""
        summary = get_results_summary([])
        
        assert summary['mean_latency_ms'] == 0.0
        assert summary['std_latency_ms'] == 0.0
        assert summary['mean_peak_ram_mb'] == 0.0
        assert summary['std_peak_ram_mb'] == 0.0

class TestSaveResultsToFile:
    """Tests for save_results_to_file function."""

    def test_save_results_to_file_creates_file(self):
        """Test that save_results_to_file creates a file."""
        import tempfile
        import json
        
        results = [
            {'latency_ms': 100.0, 'peak_ram_mb': 50.0},
            {'latency_ms': 200.0, 'peak_ram_mb': 100.0}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            save_results_to_file(results, filepath)
            
            # Verify file exists and contains valid JSON
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 2
            assert loaded[0]['latency_ms'] == 100.0
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

class TestIntegration:
    """Integration tests for the profiling module."""

    def test_full_profiling_workflow(self):
        """Test a complete profiling workflow."""
        @profile_execution
        def workload():
            data = [i * 2 for i in range(1000)]
            return sum(data)
        
        # Run profiling
        result = workload()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'latency_ms' in result
        assert 'peak_ram_mb' in result
        assert result['latency_ms'] >= 0.0
        assert result['peak_ram_mb'] >= 0.0

    def test_multiple_profiling_runs(self):
        """Test multiple profiling runs in sequence."""
        results = []
        
        @profile_execution
        def dummy_work():
            time.sleep(0.01)
            return None
        
        for _ in range(3):
            result = dummy_work()
            results.append(result)
        
        # All results should have correct structure
        for result in results:
            assert isinstance(result, dict)
            assert 'latency_ms' in result
            assert 'peak_ram_mb' in result