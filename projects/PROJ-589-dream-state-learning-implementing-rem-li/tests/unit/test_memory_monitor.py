"""
Unit tests for the memory_monitor module.
"""
import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Import the module under test
# Adjust path if running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from utils.memory_monitor import (
    get_current_rss_bytes,
    set_memory_limit_gb,
    check_and_abort_if_over_limit,
    get_peak_rss_gb,
    reset_peak_tracker,
    start_monitoring,
    _peak_rss_bytes,
    _limit_bytes,
    _monitoring_active
)


class TestMemoryMonitor(unittest.TestCase):

    def setUp(self):
        """Reset global state before each test."""
        import utils.memory_monitor as mm
        mm._peak_rss_bytes = 0
        mm._limit_bytes = None
        mm._monitoring_active = False

    def tearDown(self):
        """Clean up after each test."""
        pass

    @patch('builtins.open', new_callable=mock_open, read_data="VmRSS:     1024 kB\n")
    def test_get_current_rss_bytes(self, mock_file):
        """Test reading RSS from /proc/self/status."""
        with patch('os.path.exists', return_value=True):
            rss = get_current_rss_bytes()
            self.assertEqual(rss, 1024 * 1024) # 1024 kB -> bytes

    @patch('os.path.exists', return_value=False)
    def test_get_current_rss_bytes_no_proc(self, mock_exists):
        """Test that RuntimeError is raised on non-Linux systems."""
        with self.assertRaises(RuntimeError) as context:
            get_current_rss_bytes()
        self.assertIn("only supported on Linux", str(context.exception))

    def test_set_memory_limit_gb(self):
        """Test setting a memory limit."""
        set_memory_limit_gb(2.0)
        import utils.memory_monitor as mm
        self.assertEqual(mm._limit_bytes, 2 * 1024 * 1024 * 1024)
        self.assertTrue(mm._monitoring_active)

    def test_set_memory_limit_gb_invalid(self):
        """Test that negative limit raises ValueError."""
        with self.assertRaises(ValueError):
            set_memory_limit_gb(-1.0)

    @patch('utils.memory_monitor.get_current_rss_bytes', return_value=100)
    def test_update_peak_rss(self, mock_get_rss):
        """Test peak RSS tracking updates correctly."""
        import utils.memory_monitor as mm
        mm._peak_rss_bytes = 50
        mm.update_peak_rss()
        self.assertEqual(mm._peak_rss_bytes, 100)

    @patch('utils.memory_monitor.get_current_rss_bytes', return_value=100)
    def test_update_peak_rss_no_increase(self, mock_get_rss):
        """Test peak RSS does not decrease."""
        import utils.memory_monitor as mm
        mm._peak_rss_bytes = 200
        mm.update_peak_rss()
        self.assertEqual(mm._peak_rss_bytes, 200)

    @patch('utils.memory_monitor.update_peak_rss')
    def test_check_and_abort_no_limit_set(self, mock_update):
        """Test that no abort occurs if limit is not set."""
        import utils.memory_monitor as mm
        mm._limit_bytes = None
        mm._monitoring_active = False
        # Should not raise
        check_and_abort_if_over_limit()
        mock_update.assert_not_called()

    @patch('utils.memory_monitor.update_peak_rss', return_value=1000)
    @patch('os._exit')
    def test_check_and_abort_exceeds_limit(self, mock_exit, mock_update):
        """Test that sys.exit is called when limit is exceeded."""
        import utils.memory_monitor as mm
        mm._limit_bytes = 500 # Limit 500 bytes
        mm._monitoring_active = True
        
        with self.assertRaises(SystemExit) as context:
            check_and_abort_if_over_limit()
        
        self.assertEqual(context.exception.code, 1)
        mock_exit.assert_called_once_with(1)

    def test_get_peak_rss_gb(self):
        """Test peak RSS conversion to GB."""
        import utils.memory_monitor as mm
        mm._peak_rss_bytes = 1024 * 1024 * 1024 * 2 # 2 GB
        self.assertEqual(get_peak_rss_gb(), 2.0)

    def test_reset_peak_tracker(self):
        """Test resetting the peak tracker."""
        import utils.memory_monitor as mm
        mm._peak_rss_bytes = 1000
        reset_peak_tracker()
        self.assertEqual(mm._peak_rss_bytes, 0)

    def test_start_monitoring(self):
        """Test the convenience start function."""
        start_monitoring(4.0)
        import utils.memory_monitor as mm
        self.assertEqual(mm._limit_bytes, 4 * 1024 * 1024 * 1024)
        self.assertTrue(mm._monitoring_active)
        self.assertEqual(mm._peak_rss_bytes, 0) # Should reset on start

if __name__ == '__main__':
    unittest.main()