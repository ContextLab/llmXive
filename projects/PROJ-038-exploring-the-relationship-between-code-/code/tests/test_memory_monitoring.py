import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Import the modules to test
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.ingest import get_current_memory_usage_bytes, validate_ram_limit, MemoryLimitExceeded
from src.metrics import get_current_memory_usage_bytes as metrics_get_memory, validate_ram_limit as metrics_validate_ram

class TestMemoryMonitoring:
    """Test memory monitoring functionality in ingest and metrics modules."""

    def test_get_current_memory_usage_bytes_returns_int(self):
        """Test that get_current_memory_usage_bytes returns an integer."""
        # This will either return a real value or 0 (fallback)
        usage = get_current_memory_usage_bytes()
        assert isinstance(usage, int)
        assert usage >= 0

    def test_validate_ram_limit_passes_when_under_limit(self):
        """Test that validate_ram_limit passes when memory is under the limit."""
        # Mock a low memory usage
        with patch('src.ingest.get_current_memory_usage_bytes', return_value=1024 * 1024 * 100):  # 100MB
            # Should not raise
            validate_ram_limit(max_bytes=1024 * 1024 * 1024)  # 1GB limit

    def test_validate_ram_limit_raises_when_over_limit(self):
        """Test that validate_ram_limit raises MemoryLimitExceeded when over limit."""
        # Mock a high memory usage
        with patch('src.ingest.get_current_memory_usage_bytes', return_value=1024 * 1024 * 1024 * 8):  # 8GB
            with pytest.raises(MemoryLimitExceeded):
                validate_ram_limit(max_bytes=1024 * 1024 * 1024 * 4)  # 4GB limit

    def test_metrics_module_memory_functions_exist(self):
        """Test that metrics module has the same memory functions."""
        # Check that the functions exist and have the same signature
        assert callable(metrics_get_memory)
        assert callable(metrics_validate_ram)

    def test_metrics_validate_ram_limit_passes_when_under_limit(self):
        """Test that metrics module's validate_ram_limit passes when memory is under the limit."""
        with patch('src.metrics.get_current_memory_usage_bytes', return_value=1024 * 1024 * 100):
            metrics_validate_ram(max_bytes=1024 * 1024 * 1024)

    def test_metrics_validate_ram_limit_raises_when_over_limit(self):
        """Test that metrics module's validate_ram_limit raises when over limit."""
        with patch('src.metrics.get_current_memory_usage_bytes', return_value=1024 * 1024 * 1024 * 8):
            with pytest.raises(MemoryLimitExceeded):
                metrics_validate_ram(max_bytes=1024 * 1024 * 1024 * 4)

    def test_memory_limit_exceeded_exception_has_message(self):
        """Test that MemoryLimitExceeded exception contains a descriptive message."""
        with patch('src.ingest.get_current_memory_usage_bytes', return_value=1024 * 1024 * 1024 * 8):
            try:
                validate_ram_limit(max_bytes=1024 * 1024 * 1024 * 4)
                assert False, "Should have raised MemoryLimitExceeded"
            except MemoryLimitExceeded as e:
                assert "Memory limit exceeded" in str(e)
                assert "GB" in str(e)