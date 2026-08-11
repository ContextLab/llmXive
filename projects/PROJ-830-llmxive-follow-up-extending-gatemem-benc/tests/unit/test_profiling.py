"""
Unit tests for profiling utilities.
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
    measure_execution
)

class TestProfileResult:
    """Tests for ProfileResult dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ProfileResult(
            operation_name="test_op",
            start_time=1000.0,
            end_time=1001.0,
            duration_ms=1000.0,
            peak_memory_mb=50.0,
            memory_delta_mb=5.0,
            thread_id=12345
        )
        
        d = result.to_dict()
        
        assert d["operation_name"] == "test_op"
        assert d["start_time"] == 1000.0
        assert d["end_time"] == 1001.0
        assert d["duration_ms"] == 1000.0
        assert d["peak_memory_mb"] == 50.0
        assert d["memory_delta_mb"] == 5.0
        assert d["thread_id"] == 12345

class TestMemoryFunctions:
    """Tests for memory measurement functions."""
    
    def test_get_process_memory_mb_returns_positive(self):
        """Test that memory measurement returns positive value."""
        memory = get_process_memory_mb()
        assert isinstance(memory, float)
        assert memory >= 0.0
    
    def test_get_peak_memory_mb_initial(self):
        """Test initial peak memory is zero before profiling."""
        reset_profiling()
        peak = get_peak_memory_mb()
        assert peak == 0.0

class TestProfilingLifecycle:
    """Tests for profiling start/stop lifecycle."""
    
    def test_start_and_stop(self):
        """Test basic start and stop."""
        start_profiling("test_op")
        result = stop_profiling("test_op")
        
        assert result is not None
        assert result.operation_name == "test_op"
        assert result.duration_ms >= 0
        assert result.peak_memory_mb >= 0
    
    def test_stop_without_start(self):
        """Test stopping without starting returns None."""
        reset_profiling()
        result = stop_profiling("nonexistent")
        assert result is None
    
    def test_double_start(self):
        """Test that double start logs warning and doesn't overwrite."""
        start_profiling("first")
        start_profiling("second")  # Should log warning
        
        result = stop_profiling("first")
        assert result is not None
        
        # Second stop should return None as it was already stopped
        result2 = stop_profiling("second")
        assert result2 is None

class TestProfileBlock:
    """Tests for context manager profiling."""
    
    def test_profile_block_basic(self):
        """Test basic context manager usage."""
        with profile_block("context_test") as result:
            time.sleep(0.01)
        
        assert result is not None
        assert result.operation_name == "context_test"
        assert result.duration_ms >= 10  # At least 10ms
        assert result.duration_ms < 1000  # Reasonable upper bound
    
    def test_profile_block_with_exception(self):
        """Test that profiling continues even if exception occurs."""
        try:
            with profile_block("exception_test") as result:
                time.sleep(0.01)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Result should still be captured
        assert result is not None
        assert result.duration_ms >= 10

class TestProfileFunction:
    """Tests for function decorator profiling."""
    
    def test_profile_function_decorator(self):
        """Test that decorator profiles function execution."""
        @profile_function("decorated_test")
        def sample_func():
            time.sleep(0.01)
            return "success"
        
        result = sample_func()
        assert result == "success"
    
    def test_profile_function_preserves_metadata(self):
        """Test that decorator preserves function metadata."""
        @profile_function("meta_test")
        def sample_func():
            """Sample docstring."""
            pass
        
        assert sample_func.__name__ == "sample_func"
        assert sample_func.__doc__ == "Sample docstring."

class TestMeasureExecution:
    """Tests for direct execution measurement."""
    
    def test_measure_execution_success(self):
        """Test successful measurement of function execution."""
        def sample_func():
            time.sleep(0.01)
            return 42
        
        result, metrics = measure_execution(sample_func, operation_name="measure_test")
        
        assert result == 42
        assert metrics is not None
        assert metrics.operation_name == "measure_test"
        assert metrics.duration_ms >= 10
    
    def test_measure_execution_with_args(self):
        """Test measurement with function arguments."""
        def add_func(a, b):
            time.sleep(0.01)
            return a + b
        
        result, metrics = measure_execution(add_func, 5, 3, operation_name="add_test")
        
        assert result == 8
        assert metrics.duration_ms >= 10
    
    def test_measure_execution_with_kwargs(self):
        """Test measurement with keyword arguments."""
        def multiply_func(x, y=2):
            time.sleep(0.01)
            return x * y
        
        result, metrics = measure_execution(
            multiply_func, 5, y=3, operation_name="multiply_test"
        )
        
        assert result == 15
        assert metrics.duration_ms >= 10
    
    def test_measure_execution_propagates_exception(self):
        """Test that exceptions from function are propagated."""
        def failing_func():
            raise RuntimeError("Intentional failure")
        
        with pytest.raises(RuntimeError, match="Intentional failure"):
            measure_execution(failing_func, operation_name="fail_test")

class TestResetProfiling:
    """Tests for profiling reset functionality."""
    
    def test_reset_clears_state(self):
        """Test that reset clears all profiling state."""
        start_profiling("temp")
        # Capture some state
        _ = get_peak_memory_mb()
        
        reset_profiling()
        
        # Should be back to initial state
        peak = get_peak_memory_mb()
        assert peak == 0.0
        
        # Should be able to start fresh
        start_profiling("fresh")
        result = stop_profiling("fresh")
        assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])