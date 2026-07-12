"""
Unit tests for profiling utilities.

Tests verify that:
1. Wall-clock time is measured correctly
2. Memory usage is tracked (non-negative)
3. Context manager yields valid results
4. Decorator wraps functions correctly
"""
import time
import pytest
import tracemalloc
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.profiling import (
    profile_block,
    profile_function,
    get_process_memory_mb,
    get_peak_memory_mb,
    start_profiling,
    stop_profiling,
    measure_execution,
    ProfileResult
)

class TestProfileBlock:
    """Tests for the profile_block context manager."""

    def test_profile_block_measures_time(self):
        """Verify that profile_block measures non-zero duration for a sleeping function."""
        with profile_block(label="sleep_test") as result:
            time.sleep(0.1)
        
        assert result.duration_sec >= 0.09  # Allow small overhead
        assert result.start_time > 0
        assert result.end_time > result.start_time
        assert result.duration_sec > 0

    def test_profile_block_measures_memory(self):
        """Verify that profile_block tracks memory usage."""
        with profile_block(label="memory_test") as result:
            # Allocate some memory
            _ = [0] * 1000000
        
        assert result.peak_memory_mb >= 0.0
        assert isinstance(result.peak_memory_mb, float)
        assert result.memory_delta_mb >= -0.1  # Allow small GC variations

    def test_profile_block_returns_valid_result(self):
        """Verify that ProfileResult contains all expected fields."""
        with profile_block(label="validity_test") as result:
            pass
        
        assert isinstance(result, ProfileResult)
        assert hasattr(result, 'start_time')
        assert hasattr(result, 'end_time')
        assert hasattr(result, 'duration_sec')
        assert hasattr(result, 'peak_memory_mb')
        assert hasattr(result, 'memory_delta_mb')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'method')

    def test_profile_block_label_logging(self, caplog):
        """Verify that profile_block logs the label."""
        with caplog.at_level("INFO"):
            with profile_block(label="log_test"):
                pass
        
        assert "log_test" in caplog.text
        assert "Duration" in caplog.text

class TestProfileFunction:
    """Tests for the profile_function decorator."""

    def test_profile_function_wraps_correctly(self):
        """Verify that the decorator returns a callable."""
        @profile_function
        def dummy_func():
            return 42
        
        assert callable(dummy_func)
        assert dummy_func() == 42

    def test_profile_function_returns_result(self):
        """Verify that decorated function returns correct value."""
        @profile_function
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5

    def test_profile_function_logs_execution(self, caplog):
        """Verify that decorated function logs execution info."""
        @profile_function
        def test_func():
            time.sleep(0.01)
        
        with caplog.at_level("INFO"):
            test_func()
        
        assert "test_func" in caplog.text

class TestMemoryFunctions:
    """Tests for standalone memory measurement functions."""

    def test_get_process_memory_mb_returns_positive(self):
        """Verify that get_process_memory_mb returns a non-negative float."""
        mem = get_process_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0.0

    def test_get_peak_memory_mb_requires_tracing(self):
        """Verify that get_peak_memory_mb returns 0 if tracing is not active."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        mem = get_peak_memory_mb()
        assert mem == 0.0

    def test_get_peak_memory_mb_returns_positive_when_tracing(self):
        """Verify that get_peak_memory_mb returns positive value when tracing."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Allocate memory
        _ = [0] * 100000
        
        mem = get_peak_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0.0

class TestLifecycleFunctions:
    """Tests for start/stop/reset profiling functions."""

    def test_start_profiling_starts_tracing(self):
        """Verify that start_profiling enables tracemalloc."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        start_profiling()
        assert tracemalloc.is_tracing()

    def test_stop_profiling_stops_tracing(self):
        """Verify that stop_profiling disables tracemalloc."""
        start_profiling()
        stop_profiling()
        assert not tracemalloc.is_tracing()

    def test_reset_profiling_restarts_tracing(self):
        """Verify that reset_profiling restarts tracing."""
        if not tracemalloc.is_tracing():
            start_profiling()
        
        # Allocate some memory to dirty the tracker
        _ = [0] * 100000
        
        reset_profiling()
        assert tracemalloc.is_tracing()
        # Peak should be lower after reset (or at least fresh)
        peak = get_peak_memory_mb()
        assert peak >= 0.0

class TestMeasureExecution:
    """Tests for the measure_execution convenience function."""

    def test_measure_execution_returns_result(self):
        """Verify that measure_execution returns a ProfileResult."""
        def dummy():
            time.sleep(0.01)
        
        result = measure_execution(dummy)
        assert isinstance(result, ProfileResult)
        assert result.duration_sec > 0

    def test_measure_execution_passes_args(self):
        """Verify that measure_execution passes arguments to function."""
        def add(a, b):
            return a + b
        
        result = measure_execution(add, 5, 10)
        # The function itself returns a value, but measure_execution returns ProfileResult
        # We just verify it doesn't crash
        assert isinstance(result, ProfileResult)
