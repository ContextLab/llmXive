"""
Unit tests for the memory_monitor module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.memory_monitor import (
    get_current_memory_usage_gb,
    check_memory_threshold,
    trigger_gc,
    downsample_data,
    MEMORY_THRESHOLD_GB
)


class TestMemoryMonitor(unittest.TestCase):

    @patch('psutil.Process')
    def test_get_current_memory_usage_gb(self, mock_process):
        """Test that memory usage is calculated correctly in GB."""
        mock_process.return_value.memory_info.return_value.rss = 1024**3  # 1 GB
        usage = get_current_memory_usage_gb()
        self.assertEqual(usage, 1.0)

    def test_check_memory_threshold_low(self):
        """Test check_memory_threshold when usage is below threshold."""
        # Mock the get_current_memory_usage_gb to return a low value
        with patch('utils.memory_monitor.get_current_memory_usage_gb', return_value=1.0):
            self.assertFalse(check_memory_threshold(6.0))

    def test_check_memory_threshold_high(self):
        """Test check_memory_threshold when usage is above threshold."""
        with patch('utils.memory_monitor.get_current_memory_usage_gb', return_value=7.0):
            self.assertTrue(check_memory_threshold(6.0))

    @patch('gc.collect')
    def test_trigger_gc(self, mock_collect):
        """Test that trigger_gc calls gc.collect."""
        mock_collect.return_value = 100
        result = trigger_gc()
        mock_collect.assert_called_once()
        self.assertEqual(result, 100)

    def test_downsample_data_invalid_fraction(self):
        """Test that downsample_data raises ValueError for invalid fraction."""
        with self.assertRaises(ValueError):
            downsample_data([], target_fraction=1.5)

    def test_downsample_data_list(self):
        """Test downsampling a list."""
        data = list(range(100))
        result = downsample_data(data, target_fraction=0.5)
        self.assertEqual(len(result), 50)

    def test_downsample_data_callable(self):
        """Test downsampling when data is provided via a callable."""
        data = list(range(100))
        result = downsample_data(lambda: data, target_fraction=0.25)
        self.assertEqual(len(result), 25)

    def test_downsample_data_unsupported_type(self):
        """Test that downsampling raises NotImplementedError for unsupported types."""
        data = {"key": "value"}  # Dict does not support slicing by length in this generic way
        with self.assertRaises(NotImplementedError):
            downsample_data(data, target_fraction=0.5)


if __name__ == '__main__':
    unittest.main()