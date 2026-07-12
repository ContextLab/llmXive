"""
Unit tests for resource_monitor.py
"""
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.resource_monitor import (
    get_ram_usage_gb,
    get_disk_usage_gb,
    check_limits,
    log_usage,
    enforce_limits,
    ResourceMonitorContext,
    RAM_LIMIT_GB,
    DISK_LIMIT_GB
)

class TestResourceMonitor(unittest.TestCase):

    def test_get_ram_usage_returns_positive(self):
        """Test that RAM usage returns a positive float."""
        ram = get_ram_usage_gb()
        self.assertIsInstance(ram, float)
        self.assertGreater(ram, 0)

    def test_get_disk_usage_returns_positive(self):
        """Test that Disk usage returns a positive float."""
        disk = get_disk_usage_gb()
        self.assertIsInstance(disk, float)
        self.assertGreater(disk, 0)

    def test_check_limits_ok(self):
        """Test check_limits returns True when under limits."""
        # Since limits are 7GB/14GB, normal execution should pass
        is_ok, msg = check_limits(raise_on_exceed=False)
        self.assertTrue(is_ok)
        self.assertIn("Resources OK", msg)

    def test_check_limits_exceed_ram(self):
        """Test check_limits raises MemoryError when RAM limit is simulated exceeded."""
        # Mock psutil to return high RAM
        with patch('utils.resource_monitor.psutil') as mock_psutil:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = (RAM_LIMIT_GB + 1) * (1024 ** 3)
            mock_psutil.Process.return_value = mock_process
            
            # Mock disk to be OK
            mock_disk = MagicMock()
            mock_disk.used = 0
            mock_psutil.disk_usage.return_value = mock_disk

            with self.assertRaises(MemoryError):
                check_limits(raise_on_exceed=True)

    def test_check_limits_exceed_disk(self):
        """Test check_limits raises SpaceError when Disk limit is simulated exceeded."""
        with patch('utils.resource_monitor.psutil') as mock_psutil:
            # Mock RAM to be OK
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 1 * (1024 ** 3)
            mock_psutil.Process.return_value = mock_process
            
            # Mock disk to be high
            mock_disk = MagicMock()
            mock_disk.used = (DISK_LIMIT_GB + 1) * (1024 ** 3)
            mock_psutil.disk_usage.return_value = mock_disk

            with self.assertRaises(Exception) as context:
                check_limits(raise_on_exceed=True)
            
            self.assertTrue("DISK CRITICAL" in str(context.exception))

    def test_log_usage_creates_file(self):
        """Test that log_usage writes to a file when path is provided."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as tmp:
            tmp_path = tmp.name

        try:
            result = log_usage(log_path=tmp_path)
            self.assertIsInstance(result, dict)
            self.assertIn('ram_gb', result)
            self.assertIn('disk_gb', result)
            
            # Verify file content
            with open(tmp_path, 'r') as f:
                content = f.read()
                self.assertIn('ResourceMonitor', content)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_context_manager(self):
        """Test ResourceMonitorContext enters and exits cleanly."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            tmp_path = tmp.name

        try:
            with ResourceMonitorContext("Test", log_path=tmp_path):
                time.sleep(0.1) # Small delay to ensure time passes
            
            # Check that log was written
            with open(tmp_path, 'r') as f:
                lines = f.readlines()
                self.assertGreaterEqual(len(lines), 2) # Entry and Exit logs
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_enforce_limits(self):
        """Test enforce_limits does not raise when under limits."""
        # Should not raise
        try:
            enforce_limits()
        except Exception:
            self.fail("enforce_limits() raised unexpectedly under normal conditions")

if __name__ == '__main__':
    unittest.main()
