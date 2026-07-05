"""
Unit tests for memory monitoring functionality.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.memory_monitor import (
    get_current_memory_usage_gb,
    run_script_with_memory_monitoring,
    MAX_MEMORY_GB
)

class TestMemoryMonitor(unittest.TestCase):
    """Test cases for memory monitoring utilities."""

    def test_get_current_memory_usage_returns_positive_value(self):
        """Test that memory usage function returns a positive value."""
        memory_gb = get_current_memory_usage_gb()
        self.assertGreater(memory_gb, 0, "Memory usage should be positive")
        self.assertLess(memory_gb, 10, "Memory usage should be reasonable (< 10GB)")

    def test_memory_limit_constant(self):
        """Test that memory limit is set correctly."""
        self.assertEqual(MAX_MEMORY_GB, 7.0, "Memory limit should be 7GB")

    @patch('psutil.Popen')
    @patch('psutil.Process')
    def test_run_script_with_monitoring_success(self, mock_process, mock_popen):
        """Test successful script execution with memory monitoring."""
        # Mock process object
        mock_proc_instance = MagicMock()
        mock_proc_instance.poll.return_value = 0  # Process finished
        mock_proc_instance.returncode = 0
        mock_proc_instance.communicate.return_value = (b"stdout", b"")
        mock_popen.return_value = mock_proc_instance
        
        # Mock current process memory
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 1024**3  # 1GB
        mock_process.return_value = mock_process_instance

        result = run_script_with_memory_monitoring("code/pipeline.py")
        
        self.assertIn("success", result)
        self.assertIn("peak_memory_gb", result)
        self.assertIn("within_limit", result)

    @patch('psutil.Popen')
    @patch('psutil.Process')
    def test_run_script_with_monitoring_failure(self, mock_process, mock_popen):
        """Test failed script execution with memory monitoring."""
        # Mock process object
        mock_proc_instance = MagicMock()
        mock_proc_instance.poll.return_value = 0
        mock_proc_instance.returncode = 1  # Failed
        mock_proc_instance.communicate.return_value = (b"", b"error")
        mock_popen.return_value = mock_proc_instance
        
        # Mock current process memory
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 1024**3
        mock_process.return_value = mock_process_instance

        result = run_script_with_memory_monitoring("code/pipeline.py")
        
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])

if __name__ == "__main__":
    unittest.main()
