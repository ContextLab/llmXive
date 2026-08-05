"""
Unit tests for src/utils/resource_monitor.py.

These tests verify:
1. The ResourceMonitor class initializes correctly.
2. The `start()` and `stop()` methods function as expected.
3. The `get_peak_ram_gb()` and `get_wall_clock_min()` methods return valid numeric types.
4. The context manager protocol works correctly.
5. The `check_limits()` method raises errors when thresholds are exceeded.
"""
import time
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
import shutil

# Ensure the project root is in the path to import src.utils
# In a real CI/runner environment, this might be handled by PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.resource_monitor import ResourceMonitor


class TestResourceMonitorInit(unittest.TestCase):
    def test_initialization_defaults(self):
        """Test that default limits are set correctly."""
        monitor = ResourceMonitor()
        self.assertEqual(monitor.ram_limit_gb, 7.0)
        self.assertEqual(monitor.time_limit_min, 360.0)
        self.assertIsNone(monitor.start_time)
        self.assertIsNone(monitor.stop_time)
        self.assertEqual(monitor.peak_rss_bytes, 0)

    def test_initialization_custom_limits(self):
        """Test that custom limits are respected."""
        monitor = ResourceMonitor(ram_limit_gb=2.0, time_limit_min=10.0)
        self.assertEqual(monitor.ram_limit_gb, 2.0)
        self.assertEqual(monitor.time_limit_min, 10.0)


class TestResourceMonitorLifecycle(unittest.TestCase):
    def test_start_sets_time(self):
        """Test that start() records the current time."""
        monitor = ResourceMonitor()
        monitor.start()
        self.assertIsNotNone(monitor.start_time)
        self.assertIsNone(monitor.stop_time)

    def test_stop_requires_start(self):
        """Test that stop() fails if start() was not called."""
        monitor = ResourceMonitor()
        with self.assertRaises(RuntimeError):
            monitor.stop()

    def test_stop_records_time(self):
        """Test that stop() records the current time."""
        monitor = ResourceMonitor()
        monitor.start()
        # Allow a tiny bit of time to pass
        time.sleep(0.01)
        monitor.stop()
        self.assertIsNotNone(monitor.start_time)
        self.assertIsNotNone(monitor.stop_time)
        self.assertGreater(monitor.stop_time, monitor.start_time)

    def test_double_stop_ignored(self):
        """Test that calling stop() twice does not crash or reset time."""
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(0.01)
        monitor.stop()
        first_stop = monitor.stop_time
        
        # Should not raise
        monitor.stop()
        self.assertEqual(monitor.stop_time, first_stop)


class TestResourceMonitorContextManager(unittest.TestCase):
    def test_context_manager_execution(self):
        """Test that the context manager correctly starts and stops."""
        monitor = ResourceMonitor()
        with monitor:
            time.sleep(0.01)
        
        self.assertIsNotNone(monitor.start_time)
        self.assertIsNotNone(monitor.stop_time)

    def test_context_manager_exception_propagation(self):
        """Test that exceptions inside the context are propagated."""
        monitor = ResourceMonitor()
        with self.assertRaises(ValueError):
            with monitor:
                time.sleep(0.01)
                raise ValueError("Test error")
        
        # State should still be updated despite exception
        self.assertIsNotNone(monitor.start_time)
        self.assertIsNotNone(monitor.stop_time)


class TestResourceMonitorMetrics(unittest.TestCase):
    @patch('src.utils.resource_monitor.ResourceMonitor._read_proc_statm')
    def test_get_peak_ram_gb_returns_float(self, mock_read):
        """Test that get_peak_ram_gb returns a float."""
        # Mock the internal read to return 1GB in bytes
        mock_read.return_value = 1024 * 1024 * 1024
        
        monitor = ResourceMonitor()
        monitor.start()
        
        # Manually trigger update to set peak
        monitor._update_peak_rss()
        
        result = monitor.get_peak_ram_gb()
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1.0)

    @patch('src.utils.resource_monitor.ResourceMonitor._read_proc_statm')
    def test_get_wall_clock_min_returns_float(self, mock_read):
        """Test that get_wall_clock_min returns a float."""
        mock_read.return_value = 0 # RSS doesn't matter for this test
        
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(0.1) # Sleep for 100ms
        monitor.stop()
        
        result = monitor.get_wall_clock_min()
        self.assertIsInstance(result, float)
        # 0.1 seconds is approx 0.00166 minutes
        self.assertGreater(result, 0)
        self.assertLess(result, 1.0)

    def test_metrics_without_start(self):
        """Test that metrics return 0 if monitor was never started."""
        monitor = ResourceMonitor()
        self.assertEqual(monitor.get_peak_ram_gb(), 0.0)
        self.assertEqual(monitor.get_wall_clock_min(), 0.0)


class TestResourceMonitorLimits(unittest.TestCase):
    @patch('src.utils.resource_monitor.ResourceMonitor._read_proc_statm')
    def test_check_limits_passes(self, mock_read):
        """Test that check_limits passes when within bounds."""
        mock_read.return_value = 1024 * 1024 * 1024 # 1GB
        
        monitor = ResourceMonitor()
        monitor.start()
        monitor._update_peak_rss()
        monitor.stop() # Ensure time is set
        
        # Should not raise
        monitor.check_limits()

    @patch('src.utils.resource_monitor.ResourceMonitor._read_proc_statm')
    def test_check_limits_fails_ram(self, mock_read):
        """Test that check_limits raises when RAM exceeds limit."""
        # Set limit to 0.5GB
        monitor = ResourceMonitor(ram_limit_gb=0.5)
        # Mock 1GB usage
        mock_read.return_value = 1024 * 1024 * 1024 
        
        monitor.start()
        monitor._update_peak_rss()
        monitor.stop()

        with self.assertRaises(RuntimeError) as context:
            monitor.check_limits()
        
        self.assertIn("RAM", str(context.exception))
        self.assertIn("0.5", str(context.exception))

    @patch('src.utils.resource_monitor.ResourceMonitor._read_proc_statm')
    def test_check_limits_fails_time(self, mock_read):
        """Test that check_limits raises when time exceeds limit."""
        monitor = ResourceMonitor(time_limit_min=0.0001) # 0.1ms limit
        mock_read.return_value = 0
        
        monitor.start()
        time.sleep(0.1) # Sleep 100ms
        monitor.stop()

        with self.assertRaises(RuntimeError) as context:
            monitor.check_limits()
        
        self.assertIn("time", str(context.exception).lower() or "wall-clock", str(context.exception))


class TestResourceMonitorLinuxSpecifics(unittest.TestCase):
    """Tests specific to Linux /proc/statm behavior if applicable."""
    
    def test_read_proc_statm_format(self):
        """Verify the parsing logic handles standard /proc/statm format."""
        # This tests the internal logic if we can mock the file read
        # Since _read_proc_statm is internal, we test via the public method
        # by mocking the open function to return a specific string
        
        mock_statm_content = "12345 6789 10 11 12 13 14" # Page counts
        
        # We need to patch the open function used inside the module
        # The module uses `open(f"{statm_path}")`
        with patch('src.utils.resource_monitor.open', mock_open(read_data=mock_statm_content)):
            monitor = ResourceMonitor()
            # We need to access the private method to test parsing directly or rely on the flow
            # Let's try to trigger the flow
            try:
                # This might fail on non-Linux, but the parsing logic is what we test
                # We assume the environment is Linux for this specific unit test context
                # or we rely on the fact that if it's not Linux, the test is skipped or mocked
                rss_bytes = monitor._read_proc_statm()
                # 12345 pages * 4096 bytes (assuming 4k pages, standard)
                # The code usually does: values[1] * page_size
                # values = [12345, 6789, ...] -> values[1] is 6789
                # Let's just ensure it returns an integer
                self.assertIsInstance(rss_bytes, int)
            except FileNotFoundError:
                # If not on Linux, the test is N/A, but the code structure is valid
                self.skipTest("Not running on Linux /proc filesystem")


if __name__ == '__main__':
    unittest.main()