"""
Unit tests for memory profiling functionality.
"""
import os
import sys
import time
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.profile_memory import (
    MemoryProfileResult,
    MemoryProfiler,
    get_current_memory_mb,
    check_memory_limit,
    profile_memory,
    profile_function,
    save_profile_result
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def setup_logging():
    """Setup basic logging for tests."""
    import logging
    logging.basicConfig(level=logging.INFO)


class TestMemoryProfileResult:
    """Tests for MemoryProfileResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a MemoryProfileResult instance."""
        result = MemoryProfileResult(
            function_name="test_func",
            start_memory_mb=100.0,
            peak_memory_mb=150.0,
            end_memory_mb=120.0,
            duration_seconds=1.5,
            timestamp="2024-01-01 12:00:00",
            pid=12345
        )
        
        assert result.function_name == "test_func"
        assert result.start_memory_mb == 100.0
        assert result.peak_memory_mb == 150.0
        assert result.duration_seconds == 1.5
        assert not result.exceeded_limit
        
    def test_result_exceeded_limit(self):
        """Test result with exceeded memory limit."""
        result = MemoryProfileResult(
            function_name="test_func",
            start_memory_mb=4000.0,
            peak_memory_mb=5100.0,
            end_memory_mb=4500.0,
            duration_seconds=1.0,
            timestamp="2024-01-01 12:00:00",
            pid=12345,
            memory_limit_mb=5000.0,
            exceeded_limit=True
        )
        
        assert result.exceeded_limit is True
        assert result.memory_limit_mb == 5000.0


class TestMemoryProfiler:
    """Tests for MemoryProfiler class."""
    
    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = MemoryProfiler(limit_mb=5000)
        assert profiler.limit_mb == 5000
        assert profiler._peak_memory_mb == 0.0
        
    def test_profiler_context_manager(self):
        """Test profiler as context manager."""
        with MemoryProfiler(limit_mb=5000) as profiler:
            profiler.start()
            # Simulate some work
            time.sleep(0.1)
            peak = profiler.stop()
            
            assert peak >= 0
            
    def test_get_memory_mb(self, setup_logging):
        """Test getting current memory."""
        profiler = MemoryProfiler()
        memory = profiler._get_memory_mb()
        assert memory >= 0
        assert isinstance(memory, float)


class TestProfileMemoryContextManager:
    """Tests for using MemoryProfiler as context manager."""
    
    def test_context_manager_basic(self, setup_logging):
        """Test basic context manager usage."""
        with MemoryProfiler(limit_mb=10000) as profiler:
            profiler.start()
            # Do some work
            data = [i for i in range(10000)]
            time.sleep(0.1)
            peak = profiler.stop()
            
            assert peak >= profiler._start_memory_mb
            assert peak > 0


class TestGetCurrentMemoryMb:
    """Tests for get_current_memory_mb function."""
    
    def test_get_current_memory(self, setup_logging):
        """Test getting current memory usage."""
        memory = get_current_memory_mb()
        assert memory >= 0
        assert isinstance(memory, float)


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""
    
    def test_within_limit(self, setup_logging):
        """Test memory check within limit."""
        # Current memory should be well within 10GB limit
        assert check_memory_limit(10000) is True
        
    def test_exceeded_limit(self, setup_logging):
        """Test memory check with very low limit."""
        # This should fail since current memory is likely > 0.1 MB
        assert check_memory_limit(0.1) is False


class TestProfileFunction:
    """Tests for profile_function decorator."""
    
    def test_profile_simple_function(self, setup_logging, temp_output_dir):
        """Test profiling a simple function."""
        def simple_func():
            time.sleep(0.1)
            return "done"
        
        result = profile_function(
            simple_func,
            limit_mb=5000,
            output_path=str(temp_output_dir / "test_profile.json")
        )
        
        assert result.function_name == "simple_func"
        assert result.duration_seconds >= 0.1
        assert result.peak_memory_mb >= 0
        
        # Check that output file was created
        output_file = temp_output_dir / "test_profile.json"
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
            assert "function_name" in data
            assert "peak_memory_mb" in data


class TestSaveProfileResult:
    """Tests for save_profile_result function."""
    
    def test_save_result(self, temp_output_dir, setup_logging):
        """Test saving profile result to file."""
        result = MemoryProfileResult(
            function_name="test",
            start_memory_mb=100.0,
            peak_memory_mb=150.0,
            end_memory_mb=120.0,
            duration_seconds=1.0,
            timestamp="2024-01-01",
            pid=12345
        )
        
        output_path = temp_output_dir / "profile_result.json"
        save_profile_result(result, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_data = json.load(f)
            assert saved_data["function_name"] == "test"
            assert saved_data["peak_memory_mb"] == 150.0


class TestIntegration:
    """Integration tests for memory profiling."""
    
    def test_full_workflow(self, temp_output_dir, setup_logging):
        """Test complete memory profiling workflow."""
        # Define a memory-intensive function
        def memory_intensive_task():
            data = []
            for i in range(100000):
                data.append([i] * 10)
            time.sleep(0.2)
            return len(data)
        
        # Profile the task
        result = profile_function(
            memory_intensive_task,
            limit_mb=5000,
            output_path=str(temp_output_dir / "integration_test.json")
        )
        
        # Verify results
        assert result.function_name == "memory_intensive_task"
        assert result.duration_seconds >= 0.2
        assert result.peak_memory_mb >= result.start_memory_mb
        assert not result.exceeded_limit  # Should be within 5GB limit
        
        # Verify output file
        output_file = temp_output_dir / "integration_test.json"
        assert output_file.exists()
        
        with open(output_file) as f:
            saved_data = json.load(f)
            assert saved_data["function_name"] == "memory_intensive_task"
            assert "peak_memory_mb" in saved_data