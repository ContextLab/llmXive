"""
Unit tests for memory_utils.py
"""
import pytest
import os
import gc
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.memory_utils import (
    get_current_memory_mb,
    check_memory_limit,
    force_gc,
    clear_memory,
    MEMORY_LIMIT_MB
)


class TestMemoryUtils:
    """Test cases for memory utility functions."""

    def test_get_current_memory_mb_returns_positive(self):
        """Test that get_current_memory_mb returns a positive number."""
        memory = get_current_memory_mb()
        assert memory >= 0, "Memory usage should be non-negative"

    def test_check_memory_limit_within_limit(self):
        """Test check_memory_limit when within limit."""
        # Use a limit much higher than current usage
        result = check_memory_limit(limit_mb=100000)
        assert result is True

    def test_check_memory_limit_exceeds_limit(self):
        """Test check_memory_limit when exceeding limit."""
        # Use a very low limit to force failure
        result = check_memory_limit(limit_mb=0.001)
        assert result is False

    def test_force_gc_returns_integer(self):
        """Test that force_gc returns an integer."""
        collected = force_gc()
        assert isinstance(collected, int)
        assert collected >= 0

    def test_clear_memory_executes_without_error(self):
        """Test that clear_memory executes without raising exceptions."""
        # Should not raise any errors
        clear_memory()

    def test_memory_limit_constant(self):
        """Test that MEMORY_LIMIT_MB is set to 7000."""
        assert MEMORY_LIMIT_MB == 7000, "Memory limit should be 7000 MB (7 GB)"

    @patch('utils.memory_utils.psutil')
    def test_get_current_memory_mb_with_psutil(self, mock_psutil):
        """Test get_current_memory_mb with mocked psutil."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024*1024*500)  # 500 MB
        mock_psutil.Process.return_value = mock_process

        # Call function
        memory = get_current_memory_mb()

        # Verify result
        assert memory == 500.0, "Should return 500.0 MB"

    def test_check_memory_limit_with_default(self):
        """Test check_memory_limit uses default limit."""
        # This should work with default limit (7000 MB)
        result = check_memory_limit()
        assert result is True  # Assuming we're under 7GB