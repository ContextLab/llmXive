"""
Unit tests for ResourceMonitor functionality.

These tests verify:
- Context manager entry/exit
- Memory limit enforcement logic
- Decorator functionality
- Logging behavior
"""

import os
import sys
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.resource_monitor import (
    ResourceMonitor,
    resource_monitor,
    MemoryLimitExceeded,
    get_process_memory_mb
)


class TestResourceMonitorContextManager(unittest.TestCase):
    """Tests for the ResourceMonitor context manager."""

    def test_context_manager_entry_exit(self):
        """Test that context manager enters and exits cleanly."""
        with ResourceMonitor(limit_bytes=1024 * 1024 * 1024) as monitor:
            self.assertIsNotNone(monitor._monitor_thread)
            self.assertFalse(monitor._stop_event.is_set())
            # Memory should be tracked
            self.assertGreater(monitor.get_current_memory(), 0)
        
        # After exit, thread should be stopped
        self.assertTrue(monitor._stop_event.is_set())

    def test_soft_limit_warning(self):
        """Test that soft limit warning is logged."""
        # Create a mock process with high memory
        with patch('utils.resource_monitor.psutil.Process') as mock_process:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=2 * 1024 * 1024 * 1024)  # 2GB
            mock_process.return_value = mock_instance

            with patch('utils.resource_monitor.logger') as mock_logger:
                with ResourceMonitor(
                    limit_bytes=3 * 1024 * 1024 * 1024,  # 3GB limit
                    soft_limit_factor=0.5,  # 50% = 1.5GB
                    check_interval=0.01  # Fast check
                ):
                    time.sleep(0.05)  # Let monitor run briefly
                
                # Should have logged a warning
                warning_calls = [
                    call for call in mock_logger.warning.call_args_list
                    if 'Soft limit exceeded' in str(call)
                ]
                self.assertGreater(len(warning_calls), 0)

    def test_hard_limit_termination(self):
        """Test that hard limit causes process termination."""
        with patch('utils.resource_monitor.psutil.Process') as mock_process:
            mock_instance = MagicMock()
            # Simulate memory exceeding limit
            mock_instance.memory_info.return_value = MagicMock(rss=5 * 1024 * 1024 * 1024)  # 5GB
            mock_process.return_value = mock_instance

            with patch('utils.resource_monitor.os._exit') as mock_exit:
                with ResourceMonitor(
                    limit_bytes=3 * 1024 * 1024 * 1024,  # 3GB limit
                    check_interval=0.01
                ):
                    time.sleep(0.05)
                
                # _exit should have been called
                mock_exit.assert_called_once_with(1)

    def test_log_file_creation(self):
        """Test that log file is created and populated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "memory_log.csv"
            
            with ResourceMonitor(
                limit_bytes=1024 * 1024 * 1024,
                check_interval=0.01,
                log_file=str(log_path)
            ):
                time.sleep(0.05)
            
            self.assertTrue(log_path.exists())
            with open(log_path, 'r') as f:
                content = f.read()
                self.assertIn("timestamp, memory_mb, percent_limit", content)
                self.assertGreater(len(content.split('\n')), 1)  # Header + data


class TestResourceMonitorDecorator(unittest.TestCase):
    """Tests for the resource_monitor decorator."""

    def test_decorator_applies_monitor(self):
        """Test that decorator applies memory monitoring."""
        with patch('utils.resource_monitor.psutil.Process') as mock_process:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)  # 100MB
            mock_process.return_value = mock_instance

            @resource_monitor(limit_bytes=1024 * 1024 * 1024, check_interval=0.01)
            def test_func():
                return "success"

            result = test_func()
            self.assertEqual(result, "success")

    def test_decorator_exception_propagation(self):
        """Test that exceptions are propagated correctly."""
        with patch('utils.resource_monitor.psutil.Process') as mock_process:
            mock_instance = MagicMock()
            mock_instance.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)
            mock_process.return_value = mock_instance

            @resource_monitor(limit_bytes=1024 * 1024 * 1024, check_interval=0.01)
            def failing_func():
                raise ValueError("Test error")

            with self.assertRaises(ValueError) as context:
                failing_func()
            
            self.assertEqual(str(context.exception), "Test error")


class TestUtilityFunctions(unittest.TestCase):
    """Tests for utility functions."""

    def test_get_process_memory_mb(self):
        """Test that get_process_memory_mb returns a positive number."""
        mem_mb = get_process_memory_mb()
        self.assertGreater(mem_mb, 0)
        self.assertIsInstance(mem_mb, float)


if __name__ == '__main__':
    unittest.main()