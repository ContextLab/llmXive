"""
Unit tests for profiling utilities.
"""
import pytest
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.profiling import (
    profile_execution,
    ProfileResult,
    start_profiling,
    stop_profiling,
    reset_profiling,
    profile_block,
    get_process_memory_mb,
    get_peak_memory_mb
)


class TestProfileExecution:
    """Tests for profile_execution function."""

    def test_profile_execution_returns_dict(self):
        """Verify profile_execution returns a dict with required keys."""
        def dummy_func():
            time.sleep(0.01)
            return "done"
        
        result = profile_execution(dummy_func)
        
        assert isinstance(result, ProfileResult)
        assert hasattr(result, 'latency_ms')
        assert hasattr(result, 'peak_ram_mb')
        assert isinstance(result.latency_ms, float)
        assert isinstance(result.peak_ram_mb, float)
        assert result.latency_ms >= 0
        assert result.peak_ram_mb >= 0

    def test_profile_execution_latency_positive(self):
        """Verify profiling captures non-zero latency for a sleep."""
        def slow_func():
            time.sleep(0.1)
        
        result = profile_execution(slow_func)
        
        # Allow some tolerance for system variability
        assert result.latency_ms >= 90  # 100ms - 10% tolerance

    def test_profile_execution_memory_positive(self):
        """Verify profiling captures memory usage."""
        def memory_func():
            data = [0] * 10000
            time.sleep(0.01)
            return data
        
        result = profile_execution(memory_func)
        
        # Memory should be positive (even if small)
        assert result.peak_ram_mb > 0

    def test_profile_execution_context_manager(self):
        """Test the profile_block context manager directly."""
        with profile_block() as result:
            time.sleep(0.02)
        
        assert isinstance(result, ProfileResult)
        assert result.latency_ms >= 18  # 20ms - 10% tolerance
        assert result.peak_ram_mb >= 0

    def test_profile_execution_multiple_calls(self):
        """Verify consistent results across multiple calls."""
        def constant_func():
            time.sleep(0.01)
        
        results = [profile_execution(constant_func) for _ in range(5)]
        
        assert all(isinstance(r, ProfileResult) for r in results)
        assert all(r.latency_ms >= 0 for r in results)
        assert all(r.peak_ram_mb >= 0 for r in results)

    def test_profile_execution_with_exception(self):
        """Verify profiling handles exceptions gracefully."""
        def failing_func():
            time.sleep(0.01)
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError):
            profile_execution(failing_func)
        
        # Profiling state should be clean after exception
        result = profile_execution(lambda: time.sleep(0.01))
        assert isinstance(result, ProfileResult)


class TestProfileResult:
    """Tests for ProfileResult dataclass."""

    def test_to_dict(self):
        """Verify to_dict returns correct keys."""
        result = ProfileResult(latency_ms=100.5, peak_ram_mb=50.2)
        d = result.to_dict()
        
        assert 'latency_ms' in d
        assert 'peak_ram_mb' in d
        assert d['latency_ms'] == 100.5
        assert d['peak_ram_mb'] == 50.2

    def test_dict_values_types(self):
        """Verify dictionary values are floats."""
        result = ProfileResult(latency_ms=100, peak_ram_mb=50)
        d = result.to_dict()
        
        assert isinstance(d['latency_ms'], float)
        assert isinstance(d['peak_ram_mb'], float)


class TestMemoryFunctions:
    """Tests for memory-related helper functions."""

    def test_get_process_memory_mb(self):
        """Verify memory function returns a non-negative float."""
        mem = get_process_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0

    def test_get_peak_memory_mb(self):
        """Verify peak memory function returns a non-negative float."""
        start_profiling()
        data = [0] * 100000
        mem = get_peak_memory_mb()
        stop_profiling()
        
        assert isinstance(mem, float)
        assert mem >= 0
        # Should be greater than 0 since we allocated data
        assert mem > 0


class TestProfilerLifecycle:
    """Tests for profiler start/stop/reset."""

    def test_start_stop_cycle(self):
        """Verify start/stop cycle works correctly."""
        start_profiling()
        time.sleep(0.01)
        stop_profiling()
        
        # Should be able to start again
        start_profiling()
        result = profile_execution(lambda: time.sleep(0.01))
        stop_profiling()
        
        assert isinstance(result, ProfileResult)

    def test_reset_profiling(self):
        """Verify reset clears state."""
        start_profiling()
        data = [0] * 100000
        reset_profiling()
        
        # Should be able to profile new allocation
        result = profile_execution(lambda: time.sleep(0.01))
        assert isinstance(result, ProfileResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])