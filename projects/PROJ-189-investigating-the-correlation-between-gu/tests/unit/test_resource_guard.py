"""
Unit tests for the resource_guard module.
"""
import pytest
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code')))

from utils.resource_guard import (
    check_cpu_only,
    check_memory_limit_guard,
    time_limit_guard,
    resource_guard,
    run_with_resource_limits,
    DEFAULT_MAX_MEMORY_MB,
    DEFAULT_MAX_TIME_SECONDS
)
from utils.logging import get_logger

logger = get_logger(__name__)

class TestCpuOnly:
    def test_check_cpu_only_no_gpu(self):
        """Test that check_cpu_only returns True when no GPU is detected."""
        # Mock all GPU libraries to not be available
        with patch.dict('sys.modules', {
            'torch': None,
            'tensorflow': None,
            'jax': None
        }):
            result = check_cpu_only()
            assert result is True

    def test_check_cpu_only_with_torch_gpu(self):
        """Test that check_cpu_only warns and sets env var when CUDA is available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            with patch('utils.resource_guard.os.environ', new_callable=dict) as mock_env:
                result = check_cpu_only()
                assert result is True
                # Verify CUDA_VISIBLE_DEVICES was set
                assert mock_env.get('CUDA_VISIBLE_DEVICES') == ''

class TestMemoryGuard:
    def test_check_memory_limit_guard_success(self):
        """Test that check_memory_limit_guard passes when under limit."""
        # Mock get_memory_usage_mb to return a low value
        with patch('utils.resource_guard.get_memory_usage_mb', return_value=100.0):
            # Should not raise
            check_memory_limit_guard(limit_mb=1024)

    def test_check_memory_limit_guard_failure(self):
        """Test that check_memory_limit_guard raises MemoryError when over limit."""
        # Mock get_memory_usage_mb to return a high value
        with patch('utils.resource_guard.get_memory_usage_mb', return_value=2048.0):
            with pytest.raises(MemoryError, match="Memory limit exceeded"):
                check_memory_limit_guard(limit_mb=1024)

class TestTimeGuard:
    def test_time_limit_guard_success(self):
        """Test that time_limit_guard passes when under limit."""
        time_limit_guard._start_time = time.time() - 1.0  # 1 second ago
        # Should not raise
        time_limit_guard(limit_seconds=10)

    def test_time_limit_guard_failure(self):
        """Test that time_limit_guard raises TimeoutError when over limit."""
        time_limit_guard._start_time = time.time() - 20.0  # 20 seconds ago
        with pytest.raises(TimeoutError, match="Time limit exceeded"):
            time_limit_guard(limit_seconds=10)

class TestResourceGuardContext:
    def test_resource_guard_context_success(self):
        """Test that resource_guard context manager works for valid execution."""
        with patch('utils.resource_guard.get_memory_usage_mb', return_value=100.0):
            with resource_guard(max_memory_mb=1024, max_time_seconds=10):
                time.sleep(0.1)
                # If we get here, the context worked

    def test_resource_guard_context_memory_failure(self):
        """Test that resource_guard context manager fails on memory limit."""
        with patch('utils.resource_guard.get_memory_usage_mb', return_value=2048.0):
            with pytest.raises(MemoryError):
                with resource_guard(max_memory_mb=1024, max_time_seconds=10):
                    pass

    def test_resource_guard_context_time_failure(self):
        """Test that resource_guard context manager fails on time limit."""
        # Mock time.time to simulate time passing
        original_time = time.time
        start = time.time()
        call_count = [0]
        
        def mock_time():
            call_count[0] += 1
            if call_count[0] == 1:
                return start
            return start + 20.0  # Simulate 20 seconds passed on second call

        with patch('utils.resource_guard.get_memory_usage_mb', return_value=100.0):
            with patch('utils.resource_guard.time.time', side_effect=mock_time):
                with pytest.raises(TimeoutError):
                    with resource_guard(max_memory_mb=1024, max_time_seconds=10):
                        pass

class TestRunWithResourceLimits:
    def test_run_with_resource_limits_success(self):
        """Test that run_with_resource_limits executes function successfully."""
        def dummy_func(x):
            return x * 2

        with patch('utils.resource_guard.get_memory_usage_mb', return_value=100.0):
            result = run_with_resource_limits(
                dummy_func, 
                5, 
                max_memory_mb=1024, 
                max_time_seconds=10
            )
            assert result == 10

    def test_run_with_resource_limits_memory_error(self):
        """Test that run_with_resource_limits raises MemoryError on limit."""
        def dummy_func(x):
            return x

        with patch('utils.resource_guard.get_memory_usage_mb', return_value=2048.0):
            with pytest.raises(MemoryError):
                run_with_resource_limits(
                    dummy_func, 
                    5, 
                    max_memory_mb=1024, 
                    max_time_seconds=10
                )