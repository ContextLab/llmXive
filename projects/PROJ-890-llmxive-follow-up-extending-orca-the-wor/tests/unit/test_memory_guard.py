"""
Unit tests for the memory_guard utility module.
"""

import unittest
from unittest.mock import patch, MagicMock
from code.utils.memory_guard import (
    get_available_memory_gb,
    get_memory_usage_percent,
    adjust_batch_size,
    check_memory_sufficient
)
import psutil


class TestMemoryGuard(unittest.TestCase):

    @patch('psutil.virtual_memory')
    def test_get_available_memory_gb(self, mock_virtual_memory):
        """Test conversion of available bytes to GB."""
        # Mock return value: 4GB available
        mock_virtual_memory.return_value = MagicMock(available=4 * 1024**3)
        
        result = get_available_memory_gb()
        self.assertAlmostEqual(result, 4.0, places=1)

    @patch('psutil.virtual_memory')
    def test_get_memory_usage_percent(self, mock_virtual_memory):
        """Test retrieval of memory usage percentage."""
        mock_virtual_memory.return_value = MagicMock(percent=75.5)
        
        result = get_memory_usage_percent()
        self.assertEqual(result, 75.5)

    def test_adjust_batch_size_low_memory(self):
        """Test batch size reduction when memory usage is high."""
        # Mock high memory usage (90%)
        with patch('code.utils.memory_guard.get_memory_usage_percent', return_value=90.0):
            with patch('code.utils.memory_guard.get_available_memory_gb', return_value=2.0):
                # Start with a batch size of 32
                new_size = adjust_batch_size(
                    current_batch_size=32,
                    min_batch_size=1,
                    max_batch_size=64,
                    target_usage_percent=80.0
                )
                # Should be reduced
                self.assertLess(new_size, 32)
                self.assertGreaterEqual(new_size, 1)

    def test_adjust_batch_size_high_memory(self):
        """Test batch size maintenance/increase when memory usage is low."""
        # Mock low memory usage (40%)
        with patch('code.utils.memory_guard.get_memory_usage_percent', return_value=40.0):
            with patch('code.utils.memory_guard.get_available_memory_gb', return_value=16.0):
                new_size = adjust_batch_size(
                    current_batch_size=16,
                    min_batch_size=1,
                    max_batch_size=64,
                    target_usage_percent=80.0
                )
                # Should be allowed to go up to max
                self.assertEqual(new_size, 64)

    def test_adjust_batch_size_bounds(self):
        """Test that batch size respects min and max bounds."""
        # Mock extreme high usage
        with patch('code.utils.memory_guard.get_memory_usage_percent', return_value=99.0):
            with patch('code.utils.memory_guard.get_available_memory_gb', return_value=0.5):
                # Try to reduce a huge batch size
                new_size = adjust_batch_size(
                    current_batch_size=1000,
                    min_batch_size=1,
                    max_batch_size=64
                )
                self.assertEqual(new_size, 1) # Should hit min

    def test_check_memory_sufficient(self):
        """Test memory sufficiency check."""
        # Mock 8GB available
        with patch('code.utils.memory_guard.get_available_memory_gb', return_value=8.0):
            # Should be sufficient for 4GB requirement (with 1.2 safety) -> 4.8GB needed
            is_ok, avail = check_memory_sufficient(required_gb=4.0, safety_factor=1.2)
            self.assertTrue(is_ok)
            self.assertEqual(avail, 8.0)

            # Should fail for 8GB requirement
            is_ok, avail = check_memory_sufficient(required_gb=8.0, safety_factor=1.2)
            self.assertFalse(is_ok)


if __name__ == '__main__':
    unittest.main()