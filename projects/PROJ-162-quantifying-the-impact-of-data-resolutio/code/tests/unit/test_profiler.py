"""
Unit tests for the profiler module (T008).
"""

import pytest
import time
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.profiler import (
    ResourceMetrics,
    ProfilerError,
    MemoryLimitExceededError,
    Profiler,
    profile_block,
    profile_function,
    check_memory_limit,
    get_peak_memory_mb,
    profile
)


class TestResourceMetrics:
    """Tests for ResourceMetrics dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = ResourceMetrics(
            wall_time_seconds=1.5,
            cpu_user_seconds=1.0,
            cpu_system_seconds=0.5,
            peak_memory_mb=512.0,
            current_memory_mb=480.0,
            timestamp=1234567890.0,
            memory_limit_mb=1024.0,
            exceeded_limit=False
        )

        d = metrics.to_dict()
        assert d['wall_time_seconds'] == 1.5
        assert d['cpu_user_seconds'] == 1.0
        assert d['cpu_system_seconds'] == 0.5
        assert d['peak_memory_mb'] == 512.0
        assert d['memory_limit_mb'] == 1024.0
        assert d['exceeded_limit'] is False

    def test_repr(self):
        """Test string representation."""
        metrics = ResourceMetrics(
            wall_time_seconds=1.5,
            cpu_user_seconds=1.0,
            cpu_system_seconds=0.5,
            peak_memory_mb=512.0,
            current_memory_mb=480.0,
            timestamp=1234567890.0
        )
        repr_str = repr(metrics)
        assert 'wall=1.500s' in repr_str
        assert 'cpu=1.500s' in repr_str
        assert 'peak_mem=512.00MB' in repr_str


class TestProfiler:
    """Tests for the Profiler context manager."""

    def test_profiler_basic_timing(self):
        """Test that profiler correctly measures time."""
        with Profiler() as p:
            time.sleep(0.1)

        assert p.metrics is not None
        assert p.metrics.wall_time_seconds >= 0.1
        assert p.metrics.wall_time_seconds < 0.5  # Should not be excessively long

    def test_profiler_memory_tracking(self):
        """Test that profiler tracks memory."""
        with Profiler() as p:
            # Allocate some memory
            data = [0] * 1000000

        assert p.metrics is not None
        assert p.metrics.peak_memory_mb > 0
        assert p.metrics.current_memory_mb > 0

    def test_profiler_memory_limit_exceeded(self):
        """Test that memory limit is enforced."""
        # Set a very low limit that will be exceeded
        with pytest.raises(MemoryLimitExceededError):
            with Profiler(memory_limit_mb=0.0001) as p:
                # Allocate memory
                data = [0] * 10000000

    def test_profiler_no_limit(self):
        """Test profiler without memory limit."""
        with Profiler(memory_limit_mb=None) as p:
            data = [0] * 1000000

        assert p.metrics is not None
        assert p.metrics.memory_limit_mb is None
        assert p.metrics.exceeded_limit is False

    def test_profiler_output_path(self):
        """Test that profiler saves to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.json"
            with Profiler(output_path=output_path) as p:
                time.sleep(0.01)

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert 'wall_time_seconds' in data

    def test_profiler_decorator(self):
        """Test profiler as decorator."""
        profiler = Profiler()

        @profiler
        def my_function():
            time.sleep(0.05)
            return 42

        result = my_function()
        assert result == 42
        assert profiler.metrics is not None
        assert profiler.metrics.wall_time_seconds >= 0.05


class TestProfileBlock:
    """Tests for profile_block context manager."""

    def test_profile_block_basic(self):
        """Test basic profile_block usage."""
        with profile_block() as p:
            time.sleep(0.05)

        assert p.metrics.wall_time_seconds >= 0.05

    def test_profile_block_with_limit(self):
        """Test profile_block with memory limit."""
        # This should not raise with a reasonable limit
        with profile_block(memory_limit_mb=1024) as p:
            data = [0] * 100000
            time.sleep(0.01)

        assert p.metrics.exceeded_limit is False


class TestProfileFunction:
    """Tests for profile_function decorator."""

    def test_profile_function_basic(self):
        """Test basic profile_function usage."""
        @profile_function()
        def my_func():
            time.sleep(0.05)
            return 100

        result = my_func()
        assert result == 100

    def test_profile_function_with_limit(self):
        """Test profile_function with memory limit."""
        @profile_function(memory_limit_mb=1024)
        def my_func():
            data = [0] * 100000
            return len(data)

        result = my_func()
        assert result == 100000


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    def test_check_memory_limit_pass(self):
        """Test check_memory_limit when under limit."""
        # Should not raise
        check_memory_limit(1024)

    def test_check_memory_limit_fail(self):
        """Test check_memory_limit when over limit."""
        # Set an impossibly low limit
        with pytest.raises(MemoryLimitExceededError):
            check_memory_limit(0.0001)


class TestGetPeakMemory:
    """Tests for get_peak_memory_mb function."""

    def test_get_peak_memory_positive(self):
        """Test that get_peak_memory_mb returns positive value."""
        memory = get_peak_memory_mb()
        assert memory > 0

    def test_get_peak_memory_allocation(self):
        """Test that memory increases after allocation."""
        initial = get_peak_memory_mb()
        data = [0] * 10000000
        after = get_peak_memory_mb()
        assert after >= initial


class TestProfileFunctionDuplicate:
    """Tests for the profile_function decorator with various parameters."""

    def test_profile_function_verbose(self):
        """Test profile_function with verbose output."""
        captured = []

        class MockStdout:
            def write(self, s):
                captured.append(s)

        with patch('sys.stdout', MockStdout()):
            @profile_function(verbose=True)
            def my_func():
                time.sleep(0.01)

            my_func()

        # Verbose output should contain timing info
        output = ''.join(captured)
        assert 'Wall time' in output or 'wall' in output.lower()


class TestProfilerIntegration:
    """Integration tests for the profiler module."""

    def test_profiler_with_exception(self):
        """Test that profiler handles exceptions correctly."""
        with pytest.raises(ValueError):
            with Profiler() as p:
                raise ValueError("Test error")

        # Metrics should still be recorded
        assert p.metrics is not None
        assert p.metrics.wall_time_seconds > 0

    def test_profiler_nested(self):
        """Test nested profiler usage."""
        with Profiler() as outer:
            time.sleep(0.01)
            with Profiler() as inner:
                time.sleep(0.01)

        assert outer.metrics is not None
        assert inner.metrics is not None
        # Outer time should be greater than inner
        assert outer.metrics.wall_time_seconds >= inner.metrics.wall_time_seconds

    def test_profiler_output_json_valid(self):
        """Test that profiler output JSON is valid and contains required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.json"
            with Profiler(output_path=output_path) as p:
                time.sleep(0.01)

            with open(output_path) as f:
                data = json.load(f)

            required_fields = [
                'wall_time_seconds',
                'cpu_user_seconds',
                'cpu_system_seconds',
                'peak_memory_mb',
                'current_memory_mb',
                'timestamp'
            ]
            for field in required_fields:
                assert field in data
                assert isinstance(data[field], (int, float))

    def test_profiler_memory_limit_edge_case(self):
        """Test profiler with memory limit exactly at usage."""
        # This is a sanity check - we can't precisely control memory usage,
        # but we can verify the logic doesn't crash
        with Profiler(memory_limit_mb=1024) as p:
            # Normal usage
            data = [0] * 100000

        assert p.metrics is not None
        assert p.metrics.exceeded_limit is False

    def test_profile_decorator_syntax(self):
        """Test the @profile decorator syntax."""
        @profile(memory_limit_mb=1024)
        def my_function():
            time.sleep(0.01)
            return "done"

        result = my_function()
        assert result == "done"