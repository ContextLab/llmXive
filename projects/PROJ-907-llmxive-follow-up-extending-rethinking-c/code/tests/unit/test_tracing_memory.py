"""
Unit tests for tracing memory management.
"""
import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import torch

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils import memory_guard, get_memory_usage_gb

class TestTracingMemoryManagement:
    def test_memory_guard_pass(self):
        """Test that memory_guard returns True when usage is below threshold."""
        with patch('src.utils.get_memory_usage_gb', return_value=5.0):
            result = memory_guard(7.0)
            assert result is True

    def test_memory_guard_fail(self):
        """Test that memory_guard raises MemoryError when usage exceeds threshold."""
        with patch('src.utils.get_memory_usage_gb', return_value=8.0):
            with pytest.raises(MemoryError):
                memory_guard(7.0)

    def test_memory_usage_gb(self):
        """Test that get_memory_usage_gb returns a non-negative float."""
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0

    @patch('src.utils.gc.collect')
    @patch('src.utils.torch.cuda.empty_cache')
    def test_cleanup_memory(self, mock_empty_cache, mock_collect):
        """Test that cleanup_memory calls gc.collect and torch.cuda.empty_cache."""
        from src.utils import cleanup_memory
        if torch.cuda.is_available():
            cleanup_memory()
            mock_collect.assert_called_once()
            mock_empty_cache.assert_called_once()
        else:
            cleanup_memory()
            mock_collect.assert_called_once()
            mock_empty_cache.assert_not_called()