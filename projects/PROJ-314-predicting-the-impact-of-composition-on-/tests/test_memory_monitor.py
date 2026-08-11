"""
Unit tests for memory_monitor module.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

class TestMemoryMonitor(unittest.TestCase):

    @patch('memory_monitor.psutil')
    def test_get_memory_usage_gb_with_psutil(self, mock_psutil):
        """Test memory usage calculation when psutil is available."""
        import memory_monitor
        memory_monitor.HAS_PSUTIL = True
        
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3)  # 2GB
        mock_psutil.Process.return_value = mock_process
        
        usage = memory_monitor.get_memory_usage_gb()
        self.assertAlmostEqual(usage, 2.0, places=2)

    def test_get_memory_usage_gb_without_psutil(self):
        """Test memory usage returns 0 when psutil is not available."""
        import memory_monitor
        original_has_psutil = memory_monitor.HAS_PSUTIL
        memory_monitor.HAS_PSUTIL = False
        
        try:
            usage = memory_monitor.get_memory_usage_gb()
            self.assertEqual(usage, 0.0)
        finally:
            memory_monitor.HAS_PSUTIL = original_has_psutil

    @patch('memory_monitor.psutil')
    def test_check_memory_limit_within_limit(self, mock_psutil):
        """Test that check_memory_limit passes when under limit."""
        import memory_monitor
        memory_monitor.HAS_PSUTIL = True
        
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3)  # 2GB
        mock_psutil.Process.return_value = mock_process
        
        # Should not raise
        result = memory_monitor.check_memory_limit(limit_gb=6)
        self.assertTrue(result)

    @patch('memory_monitor.psutil')
    def test_check_memory_limit_exceeded(self, mock_psutil):
        """Test that check_memory_limit raises MemoryError when over limit."""
        import memory_monitor
        memory_monitor.HAS_PSUTIL = True
        
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 8 * (1024 ** 3)  # 8GB
        mock_psutil.Process.return_value = mock_process
        
        with self.assertRaises(MemoryError):
            memory_monitor.check_memory_limit(limit_gb=6)

    def test_force_garbage_collection(self):
        """Test that force_garbage_collection runs without error."""
        import memory_monitor
        # Should not raise
        memory_monitor.force_garbage_collection()

    def test_validate_dataset_size_within_limit(self):
        """Test dataset size validation passes when under limit."""
        import memory_monitor
        result = memory_monitor.validate_dataset_size(500.0, max_size_mb=1000.0)
        self.assertTrue(result)

    def test_validate_dataset_size_exceeded(self):
        """Test dataset size validation raises MemoryError when over limit."""
        import memory_monitor
        with self.assertRaises(MemoryError):
            memory_monitor.validate_dataset_size(1500.0, max_size_mb=1000.0)

    @patch('memory_monitor.psutil')
    def test_log_memory_usage_creates_file(self, mock_psutil):
        """Test that log_memory_usage creates the log file."""
        import memory_monitor
        memory_monitor.HAS_PSUTIL = True
        
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3)
        mock_psutil.Process.return_value = mock_process
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_memory.log"
            memory_monitor.log_memory_usage(log_file=log_file)
            
            self.assertTrue(log_file.exists())
            with open(log_file, 'r') as f:
                content = f.read()
                self.assertIn("Memory Usage:", content)

if __name__ == '__main__':
    unittest.main()