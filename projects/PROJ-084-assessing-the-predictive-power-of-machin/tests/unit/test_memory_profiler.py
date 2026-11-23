"""
Unit tests for the memory_profiler module.
"""
import pytest
import tracemalloc
import tempfile
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.memory_profiler import (
    start_profiling,
    stop_profiling,
    get_current_memory_mb,
    get_peak_memory_mb,
    check_memory_limit,
    force_gc,
    save_memory_profile_log,
    MAX_MEMORY_MB
)


class TestMemoryProfiler:
    """Test cases for memory_profiler functions."""

    def test_start_and_stop_profiling(self):
        """Test that profiling can be started and stopped."""
        start_profiling()
        assert tracemalloc.is_tracing()
        
        current, peak = stop_profiling()
        assert not tracemalloc.is_tracing()
        assert current >= 0
        assert peak >= 0

    def test_get_memory_functions(self):
        """Test that memory functions work correctly."""
        start_profiling()
        
        current = get_current_memory_mb()
        assert isinstance(current, float)
        assert current >= 0
        
        peak = get_peak_memory_mb()
        assert isinstance(peak, float)
        assert peak >= 0
        assert peak >= current
        
        stop_profiling()

    def test_check_memory_limit(self):
        """Test memory limit checking."""
        # Should pass for values below limit
        assert check_memory_limit(100.0) is True
        assert check_memory_limit(MAX_MEMORY_MB) is True
        
        # Should fail for values above limit
        assert check_memory_limit(MAX_MEMORY_MB + 100.0) is False

    def test_force_gc(self):
        """Test that force_gc runs without error."""
        force_gc()
        # Just ensure it doesn't raise an exception

    def test_save_memory_profile_log(self):
        """Test saving memory profile log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_memory_profile.log"
            
            save_memory_profile_log(
                current_mb=100.0,
                peak_mb=200.0,
                output_path=output_path,
                extra_info={"test_key": "test_value"}
            )
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "Current Memory: 100.00 MB" in content
            assert "Peak Memory: 200.00 MB" in content
            assert "test_key: test_value" in content
            assert "Status: PASS" in content

    def test_save_memory_profile_log_fail_status(self):
        """Test saving memory profile log with fail status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_memory_profile_fail.log"
            
            save_memory_profile_log(
                current_mb=100.0,
                peak_mb=MAX_MEMORY_MB + 100.0, # Exceed limit
                output_path=output_path
            )
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "Status: FAIL" in content

    def test_get_memory_without_profiling(self):
        """Test that getting memory without profiling raises an error."""
        # Ensure profiling is stopped
        if tracemalloc.is_tracing():
            stop_profiling()
        
        with pytest.raises(RuntimeError, match="tracemalloc is not tracing"):
            get_current_memory_mb()
        
        with pytest.raises(RuntimeError, match="tracemalloc is not tracing"):
            get_peak_memory_mb()