import os
import sys
import time
import json
import tempfile
import threading
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.profile_memory import (
    MemoryProfileResult,
    MemoryProfiler,
    profile_memory,
    get_current_memory_mb,
    check_memory_limit,
    profile_function,
    save_profile_result
)
from src.utils.logging import setup_default_loggers

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def setup_logging():
    """Setup logging for tests."""
    setup_default_loggers()

class TestMemoryProfileResult:
    """Tests for MemoryProfileResult dataclass."""
    
    def test_create_result(self):
        """Test creating a MemoryProfileResult instance."""
        result = MemoryProfileResult(
            function_name="test_func",
            start_time=0.0,
            end_time=1.0,
            duration_seconds=1.0,
            peak_memory_mb=100.0,
            current_memory_mb=95.0,
            memory_increase_mb=-5.0
        )
        assert result.function_name == "test_func"
        assert result.duration_seconds == 1.0
        assert result.peak_memory_mb == 100.0
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = MemoryProfileResult(
            function_name="test",
            start_time=0.0,
            end_time=1.0,
            duration_seconds=1.0,
            peak_memory_mb=50.0,
            current_memory_mb=45.0,
            memory_increase_mb=-5.0,
            return_value=42
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data['function_name'] == "test"
        assert data['return_value'] == 42

class TestMemoryProfiler:
    """Tests for MemoryProfiler class."""
    
    def test_context_manager(self):
        """Test MemoryProfiler as a context manager."""
        with MemoryProfiler("test_func") as profiler:
            # Simulate some work
            time.sleep(0.1)
        
        assert profiler.start_time > 0
        assert profiler.end_time > profiler.start_time
        assert profiler.duration_seconds > 0
    
    def test_memory_tracking(self):
        """Test that memory is actually tracked."""
        with MemoryProfiler("test_tracking") as profiler:
            # Allocate some memory
            data = [i for i in range(10000)]
            time.sleep(0.1)
        
        # Peak memory should be at least the current memory
        assert profiler.peak_memory_mb >= profiler.current_memory_mb
    
    def test_get_result(self):
        """Test get_result method."""
        with MemoryProfiler("test_result") as profiler:
            time.sleep(0.05)
            result = profiler.get_result(return_value="success")
        
        assert result.function_name == "test_result"
        assert result.return_value == "success"
        assert result.error is None

class TestProfileMemoryContextManager:
    """Tests for the context manager functionality."""
    
    def test_exception_handling(self):
        """Test that context manager handles exceptions properly."""
        try:
            with MemoryProfiler("test_exception") as profiler:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Context manager should still have timing info
        assert profiler.start_time > 0
        assert profiler.end_time > 0

class TestGetCurrentMemoryMb:
    """Tests for get_current_memory_mb function."""
    
    def test_returns_positive_value(self):
        """Test that function returns a positive memory value."""
        mem = get_current_memory_mb()
        assert mem > 0
        assert isinstance(mem, float)
    
    def test_reasonable_range(self):
        """Test that memory usage is within reasonable bounds."""
        mem = get_current_memory_mb()
        # Should be between 10MB and 10GB for a typical Python process
        assert 10 < mem < 10000

class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""
    
    def test_within_limit(self):
        """Test when memory is within limit."""
        current = get_current_memory_mb()
        # Set limit well above current usage
        assert check_memory_limit(current * 2) is True
    
    def test_exceeds_limit(self):
        """Test when memory exceeds limit."""
        current = get_current_memory_mb()
        # Set limit well below current usage
        assert check_memory_limit(current * 0.5) is False

class TestProfileFunction:
    """Tests for profile_function decorator/function."""
    
    def test_profile_function_success(self):
        """Test profiling a successful function."""
        def simple_func():
            return 42
        
        result = profile_function(simple_func)
        assert result.error is None
        assert result.function_name == "simple_func"
    
    def test_profile_function_with_args(self):
        """Test profiling a function with arguments."""
        def add_numbers(a, b):
            return a + b
        
        result = profile_function(add_numbers, 5, 10)
        assert result.error is None
        assert result.function_name == "add_numbers"
    
    def test_profile_function_error(self):
        """Test profiling a function that raises an error."""
        def failing_func():
            raise RuntimeError("Intentional error")
        
        result = profile_function(failing_func)
        assert result.error is not None
        assert "Intentional error" in result.error

class TestSaveProfileResult:
    """Tests for save_profile_result function."""
    
    def test_save_and_load(self, temp_output_dir):
        """Test saving and loading a profile result."""
        result = MemoryProfileResult(
            function_name="test_save",
            start_time=0.0,
            end_time=1.0,
            duration_seconds=1.0,
            peak_memory_mb=100.0,
            current_memory_mb=95.0,
            memory_increase_mb=-5.0,
            return_value={"key": "value"}
        )
        
        output_path = temp_output_dir / "profile.json"
        save_profile_result(result, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['function_name'] == "test_save"
        assert loaded_data['peak_memory_mb'] == 100.0
    
    def test_creates_parent_directory(self, temp_output_dir):
        """Test that parent directories are created if they don't exist."""
        result = MemoryProfileResult(
            function_name="test",
            start_time=0.0,
            end_time=1.0,
            duration_seconds=1.0,
            peak_memory_mb=50.0,
            current_memory_mb=45.0,
            memory_increase_mb=-5.0
        )
        
        deep_path = temp_output_dir / "subdir1" / "subdir2" / "profile.json"
        save_profile_result(result, deep_path)
        
        assert deep_path.exists()

class TestIntegration:
    """Integration tests for memory profiling."""
    
    def test_full_workflow(self, temp_output_dir):
        """Test a complete memory profiling workflow."""
        def memory_work():
            data = []
            for i in range(100000):
                data.append(i)
            time.sleep(0.1)
            return len(data)
        
        # Profile the function
        result = profile_function(memory_work)
        
        # Verify result
        assert result.error is None
        assert result.duration_seconds > 0
        assert result.peak_memory_mb > 0
        assert result.return_value == 100000
        
        # Save result
        output_file = temp_output_dir / "integration_profile.json"
        save_profile_result(result, output_file)
        
        # Verify file
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data['function_name'] == 'memory_work'
    
    def test_decorator_usage(self):
        """Test using the profile_memory decorator."""
        @profile_memory
        def decorated_func(x):
            time.sleep(0.05)
            return x * 2
        
        result, profile_result = decorated_func(21)
        
        assert result == 42
        assert profile_result.error is None
        assert profile_result.function_name == "decorated_func"
        assert profile_result.duration_seconds > 0