"""
Unit tests for utils/memory.py
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import psutil

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.memory import check_and_terminate_if_exceeds, get_memory_usage_gb, enable_gradient_checkpointing


class TestMemoryWatchdog(unittest.TestCase):

    @patch('utils.memory.psutil.Process')
    def test_check_below_limit(self, mock_process_class):
        """Test that process continues when memory is below limit."""
        mock_process = MagicMock()
        # 2 GB usage
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3)
        mock_process_class.return_value = mock_process

        # Should not raise
        try:
            check_and_terminate_if_exceeds(4.0)
        except SystemExit:
            self.fail("check_and_terminate_if_exceeds() raised SystemExit unexpectedly!")

    @patch('utils.memory.os._exit')
    @patch('utils.memory.psutil.Process')
    def test_check_exceeds_limit(self, mock_process_class, mock_exit):
        """Test that process terminates when memory exceeds limit."""
        mock_process = MagicMock()
        # 5 GB usage
        mock_process.memory_info.return_value.rss = 5 * (1024 ** 3)
        mock_process_class.return_value = mock_process

        with self.assertRaises(SystemExit) as context:
            check_and_terminate_if_exceeds(4.0)

        # Verify exit code is 137 (SIGKILL)
        mock_exit.assert_called_once_with(137)

    def test_get_memory_usage_gb(self):
        """Test that get_memory_usage_gb returns a positive float."""
        usage = get_memory_usage_gb()
        self.assertIsInstance(usage, float)
        self.assertGreater(usage, 0)


class TestGradientCheckpointing(unittest.TestCase):

    def test_enable_checkpointing_supported(self):
        """Test enabling checkpointing on a model that supports it."""
        mock_model = MagicMock()
        mock_model.gradient_checkpointing_enable = MagicMock()
        
        enable_gradient_checkpointing(mock_model)
        
        mock_model.gradient_checkpointing_enable.assert_called_once()

    def test_enable_checkpointing_not_supported(self):
        """Test enabling checkpointing on a model that does not support it."""
        mock_model = MagicMock(spec=[]) # No gradient_checkpointing_enable attribute
        
        # Should not raise, just log warning
        try:
            enable_gradient_checkpointing(mock_model)
        except Exception:
            self.fail("enable_gradient_checkpointing raised exception unexpectedly")


if __name__ == '__main__':
    unittest.main()