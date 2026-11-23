"""
Unit tests for memory profiling utilities.
"""
import os
import sys
import time
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from src.utils.profile_memory import (
    MemoryProfileResult,
    MemoryProfiler,
    get_current_memory_mb,
    check_memory_limit,
    profile_memory,
    profile_function,
    save_profile_result
)

# Fixtures
@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def mock_psutil():
    """Mock psutil to avoid dependency issues in tests."""
    with patch('src.utils.profile_memory.psutil') as mock_psutil:
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024 * 1024 * 100)  # 100 MB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.available = True
        yield mock_psutil


class TestMemoryProfileResult:
    """Tests for MemoryProfileResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = MemoryProfileResult(
            peak_memory_mb=100.0,
            start_memory_mb=50.0,
            end_memory_mb=60.0,
            duration_seconds=10.0,
            timestamp="2023-01-01T00:00:00",
            task_name="test_task"
        )
        d = result.to_dict()
        assert d['peak_memory_mb'] == 100.0
        assert d['task_name'] == "test_task"
        assert 'pid' in d

    def test_str_representation(self):
        """Test string representation."""
        result = MemoryProfileResult(
            peak_memory_mb=100.0,
            start_memory_mb=50.0,
            end_memory_mb=60.0,
            duration_seconds=10.0,
            timestamp="2023-01-01T00:00:00"
        )
        s = str(result)
        assert "100.00" in s
        assert "50.00" in s


class TestMemoryProfiler:
    """Tests for MemoryProfiler class."""

    def test_context_manager(self, mock_psutil):
        """Test MemoryProfiler as a context manager."""
        with MemoryProfiler(task_name="test") as profiler:
            # Simulate some work
            time.sleep(0.1)
            # Memory should be captured
            assert profiler.start_memory > 0
        
        # After exit, peak memory should be recorded
        assert profiler.peak_memory >= profiler.start_memory

    def test_manual_start_stop(self, mock_psutil):
        """Test manual start and stop."""
        profiler = MemoryProfiler(task_name="manual_test")
        profiler.start()
        time.sleep(0.1)
        result = profiler.stop()
        
        assert result.peak_memory_mb > 0
        assert result.duration_seconds > 0
        assert result.task_name == "manual_test"

    def test_memory_increases(self, mock_psutil):
        """Test that profiler detects memory increase."""
        # Mock increasing memory
        mock_psutil.Process().memory_info.side_effect = [
            MagicMock(rss=100 * 1024 * 1024), # 100 MB start
            MagicMock(rss=200 * 1024 * 1024), # 200 MB peak
            MagicMock(rss=150 * 1024 * 1024), # 150 MB end
        ]
        
        with MemoryProfiler(task_name="growth_test") as profiler:
            time.sleep(0.1)
        
        # Peak should be 200 MB
        assert profiler.peak_memory_mb >= 200.0


class TestProfileMemoryContextManager:
    """Tests for the context manager behavior."""

    def test_exception_handling(self, mock_psutil):
        """Test that profiler stops even if exception occurs."""
        with pytest.raises(ValueError):
            with MemoryProfiler(task_name="error_test") as profiler:
                raise ValueError("Simulated error")
        
        # Profiler should have stopped and recorded partial data
        # We can't easily check the result here without capturing it,
        # but the test passes if no deadlock occurs


class TestGetCurrentMemoryMb:
    """Tests for get_current_memory_mb function."""

    def test_returns_positive_value(self, mock_psutil):
        """Test that function returns a positive value."""
        memory = get_current_memory_mb()
        assert memory > 0

    def test_fallback_on_linux(self):
        """Test fallback mechanism on Linux."""
        with patch('src.utils.profile_memory.PSUTIL_AVAILABLE', False):
            with patch('src.utils.profile_memory.sys.platform', 'linux'):
                with patch('builtins.open', mock_open_with_data("VmRSS: 102400 kB")):
                    memory = get_current_memory_mb()
                    assert memory == 100.0  # 102400 / 1024


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    def test_within_limit(self, mock_psutil):
        """Test when memory is within limit."""
        result = check_memory_limit(limit_mb=200.0)
        assert result is True

    def test_exceeds_limit(self, mock_psutil):
        """Test when memory exceeds limit."""
        with pytest.raises(MemoryError):
            check_memory_limit(limit_mb=50.0)

    def test_custom_current_memory(self, mock_psutil):
        """Test with custom current memory value."""
        result = check_memory_limit(limit_mb=200.0, current_memory_mb=100.0)
        assert result is True


class TestProfileFunction:
    """Tests for profile_function decorator and utility."""

    def test_decorator(self, mock_psutil):
        """Test the profile_memory decorator."""
        @profile_memory
        def my_func():
            return 42
        
        result, profile_result = my_func()
        assert result == 42
        assert profile_result.peak_memory_mb > 0

    def test_profile_function_utility(self, mock_psutil):
        """Test the profile_function utility."""
        def my_func(x):
            return x * 2
        
        result, profile_result = profile_function(my_func, 5, task_name="test_func")
        assert result == 10
        assert profile_result.task_name == "test_func"


class TestSaveProfileResult:
    """Tests for save_profile_result function."""

    def test_save_single(self, temp_output_dir):
        """Test saving a single result."""
        result = MemoryProfileResult(
            peak_memory_mb=100.0,
            start_memory_mb=50.0,
            end_memory_mb=60.0,
            duration_seconds=10.0,
            timestamp="2023-01-01T00:00:00",
            task_name="test"
        )
        
        output_path = temp_output_dir / "profile.json"
        saved_path = save_profile_result(result, str(output_path), append=False)
        
        assert saved_path.exists()
        with open(saved_path, 'r') as f:
            data = json.load(f)
            assert data['peak_memory_mb'] == 100.0

    def test_append_mode(self, temp_output_dir):
        """Test appending multiple results."""
        result1 = MemoryProfileResult(
            peak_memory_mb=100.0,
            start_memory_mb=50.0,
            end_memory_mb=60.0,
            duration_seconds=10.0,
            timestamp="2023-01-01T00:00:00",
            task_name="test1"
        )
        result2 = MemoryProfileResult(
            peak_memory_mb=200.0,
            start_memory_mb=100.0,
            end_memory_mb=150.0,
            duration_seconds=20.0,
            timestamp="2023-01-01T00:01:00",
            task_name="test2"
        )
        
        output_path = temp_output_dir / "profile.jsonl"
        save_profile_result(result1, str(output_path), append=True)
        save_profile_result(result2, str(output_path), append=True)
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            data1 = json.loads(lines[0])
            data2 = json.loads(lines[1])
            assert data1['task_name'] == "test1"
            assert data2['task_name'] == "test2"


# Helper for mock_open
def mock_open_with_data(data):
    from unittest.mock import mock_open
    m = mock_open(read_data=data)
    return m