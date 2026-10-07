"""
Unit tests for optimization constraints (T025).
Verifies that training and evaluation respect CPU-only, time, and memory limits.
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from optimization_wrapper import (
    get_memory_usage_bytes,
    check_memory_usage,
    run_with_constraints,
    optimize_training_parameters,
    MAX_TIME_PER_AUTHOR,
    MAX_RAM_BYTES
)
from utils import get_logger

logger = get_logger(__name__)


class TestMemoryConstraints:
    """Tests for memory constraint enforcement."""

    def test_get_memory_usage_bytes(self):
        """Test that memory usage can be retrieved."""
        mem = get_memory_usage_bytes()
        assert mem >= 0, "Memory usage should be non-negative"
        logger.info(f"Current memory usage: {mem / (1024**3):.2f} GB")

    def test_check_memory_usage_no_error_under_limit(self):
        """Test that no error is raised when memory is under limit."""
        # This should not raise an exception
        check_memory_usage()

    def test_memory_warning_threshold(self):
        """Test that warning is logged when memory approaches limit."""
        # Mock memory usage to be above warning threshold but below limit
        with patch('optimization_wrapper.get_memory_usage_bytes', return_value=5.5 * 1024**3):
            # Should log a warning but not raise
            with patch('optimization_wrapper.logger.warning') as mock_warning:
                check_memory_usage()
                mock_warning.assert_called_once()


class TestTimeConstraints:
    """Tests for time constraint enforcement."""

    def test_run_with_constraints_success_within_limit(self):
        """Test that a function completing within time limit succeeds."""
        def quick_func():
            time.sleep(0.1)
            return "success"

        result = run_with_constraints(quick_func, "test_author", timeout=30)
        assert result == "success"

    def test_run_with_constraints_timeout(self):
        """Test that TimeoutError is raised when function exceeds time limit."""
        def slow_func():
            time.sleep(0.5)  # 500ms
            return "success"

        with pytest.raises(TimeoutError):
            run_with_constraints(slow_func, "test_author", timeout=0.1)

    def test_run_with_constraints_memory_error(self):
        """Test that MemoryError is raised when memory limit is exceeded."""
        def memory_intensive_func():
            # Simulate high memory usage
            with patch('optimization_wrapper.get_memory_usage_bytes', return_value=MAX_RAM_BYTES + 1):
                check_memory_usage()
            return "success"

        with pytest.raises(MemoryError):
            run_with_constraints(memory_intensive_func, "test_author", timeout=30)


class TestParameterOptimization:
    """Tests for training parameter optimization."""

    def test_optimize_training_parameters_n4(self):
        """Test parameter optimization for n=4."""
        params = optimize_training_parameters(ngram_order=4, max_documents=1000)
        assert params["ngram_range"] == (4, 4)
        assert params["max_documents"] == 1000

    def test_optimize_training_parameters_n5(self):
        """Test parameter optimization for n=5."""
        params = optimize_training_parameters(ngram_order=5, max_documents=1000)
        assert params["ngram_range"] == (5, 5)
        assert params["max_documents"] == 500  # Reduced for n=5

    def test_optimize_training_parameters_n6(self):
        """Test parameter optimization for n=6."""
        params = optimize_training_parameters(ngram_order=6, max_documents=1000)
        assert params["ngram_range"] == (6, 6)
        assert params["max_documents"] == 250  # Reduced for n=6


class TestCPUOnlyEnforcement:
    """Tests for CPU-only execution enforcement."""

    def test_cuda_visible_devices_unset(self):
        """Test that CUDA_VISIBLE_DEVICES is set to empty string."""
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
            "CUDA_VISIBLE_DEVICES should be empty for CPU-only execution"

    def test_tf_logging_suppressed(self):
        """Test that TensorFlow logging is suppressed."""
        assert os.environ.get("TF_CPP_MIN_LOG_LEVEL") == "3", \
            "TensorFlow logging should be suppressed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])