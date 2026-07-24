"""
Tests for the Resource Watchdog module.
"""
import os
import sys
import threading
import time
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.resource_watchdog import (
    ResourceLimitExceeded,
    _check_resources,
    start_watchdog,
    stop_watchdog,
    run_with_watchdog,
    check_and_kill_if_needed,
    _watchdog_active,
    _watchdog_thread
)
from code.utils.config import MAX_CPU_CORES, MAX_MEMORY_GB


class TestResourceWatchdog(unittest.TestCase):

    def setUp(self):
        """Reset watchdog state before each test."""
        global _watchdog_active, _watchdog_thread
        _watchdog_active = False
        _watchdog_thread = None

    def tearDown(self):
        """Ensure watchdog is stopped after each test."""
        stop_watchdog()
        # Force a small sleep to ensure thread cleanup
        time.sleep(0.1)

    @patch('code.utils.resource_watchdog.psutil')
    def test_check_resources_cpu_ok(self, mock_psutil):
        """Test that check_resources returns False when CPU is under limit."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0  # 50% usage, limit is 200% (2 cores)

        result = _check_resources()
        self.assertFalse(result)

    @patch('code.utils.resource_watchdog.psutil')
    def test_check_resources_cpu_exceeded(self, mock_psutil):
        """Test that check_resources returns True when CPU exceeds limit."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        mock_psutil.Process.return_value = mock_process
        # Limit is 2 cores -> 200%. Set usage to 250%.
        mock_psutil.cpu_percent.return_value = 250.0

        result = _check_resources()
        self.assertTrue(result)

    @patch('code.utils.resource_watchdog.psutil')
    def test_check_resources_ram_ok(self, mock_psutil):
        """Test that check_resources returns False when RAM is under limit."""
        # Limit is 7GB. Set usage to 1GB.
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0

        result = _check_resources()
        self.assertFalse(result)

    @patch('code.utils.resource_watchdog.psutil')
    def test_check_resources_ram_exceeded(self, mock_psutil):
        """Test that check_resources returns True when RAM exceeds limit."""
        # Limit is 7GB. Set usage to 8GB.
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 8 * (1024 ** 3)  # 8GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0

        result = _check_resources()
        self.assertTrue(result)

    @patch('code.utils.resource_watchdog.psutil')
    def test_run_with_watchdog_success(self, mock_psutil):
        """Test that run_with_watchdog executes function successfully if limits not exceeded."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0

        executed = False
        def dummy_func():
            nonlocal executed
            executed = True

        run_with_watchdog(dummy_func)
        
        self.assertTrue(executed)
        self.assertFalse(_watchdog_active)

    @patch('code.utils.resource_watchdog.psutil')
    def test_run_with_watchdog_raises_on_ram_exceeded(self, mock_psutil):
        """Test that run_with_watchdog raises ResourceLimitExceeded if RAM exceeds limit."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 8 * (1024 ** 3)  # 8GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0

        def dummy_func():
            pass

        with self.assertRaises(ResourceLimitExceeded):
            run_with_watchdog(dummy_func)

    @patch('code.utils.resource_watchdog.psutil')
    def test_run_with_watchdog_raises_on_cpu_exceeded(self, mock_psutil):
        """Test that run_with_watchdog raises ResourceLimitExceeded if CPU exceeds limit."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 250.0  # 250% > 200% limit

        def dummy_func():
            pass

        with self.assertRaises(ResourceLimitExceeded):
            run_with_watchdog(dummy_func)

    def test_check_and_kill_if_needed_ok(self):
        """Test check_and_kill_if_needed returns False when resources are ok."""
        with patch('code.utils.resource_watchdog.psutil') as mock_psutil:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 50.0

            result = check_and_kill_if_needed()
            self.assertFalse(result)

    def test_check_and_kill_if_needed_raises(self):
        """Test check_and_kill_if_needed raises when resources exceeded."""
        with patch('code.utils.resource_watchdog.psutil') as mock_psutil:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 8 * (1024 ** 3)
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 50.0

            with self.assertRaises(ResourceLimitExceeded):
                check_and_kill_if_needed()


if __name__ == '__main__':
    unittest.main()