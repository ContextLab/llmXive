import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock, PropertyMock
import psutil

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.memory import check_ram_usage, get_memory_usage_gb, MemoryWatchdog
from config import get_config


class TestMemoryWatchdog(unittest.TestCase):
    
    def setUp(self):
        # Configure logging to capture warnings
        self.logger = logging.getLogger('utils.memory')
        self.logger.setLevel(logging.DEBUG)
        self.handler = logging.StreamHandler(sys.stdout)
        self.handler.setLevel(logging.WARNING)
        self.formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        
        # Capture log output
        self.log_stream = io.StringIO()
        self.stream_handler = logging.StreamHandler(self.log_stream)
        self.stream_handler.setLevel(logging.WARNING)
        self.stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.stream_handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.logger.removeHandler(self.stream_handler)

    @patch('utils.memory.psutil.Process')
    def test_check_ram_usage_within_limit(self, mock_process):
        """
        Test that no warning is logged when RAM usage is within the limit.
        """
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 2 * (1024 ** 3)  # 2 GB
        mock_process.return_value.memory_info.return_value = mock_mem_info
        
        limit = 4.0  # 4 GB limit
        
        # Mock config to return a limit if needed, though we pass limit directly
        with patch('utils.memory.get_config') as mock_cfg:
            mock_cfg.return_value.get_ram_limit.return_value = limit
            
            result = check_ram_usage(limit)
            
            self.assertFalse(result, "Should return False when within limit")
            self.assertNotIn("RAM Warning", self.log_stream.getvalue())

    @patch('utils.memory.psutil.Process')
    def test_check_ram_usage_exceeds_limit_logs_warning(self, mock_process):
        """
        Test that a warning is logged when RAM usage exceeds the limit.
        Verification: Asserts a warning is logged with the correct peak value, 
        but no exception is raised.
        """
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 6 * (1024 ** 3)  # 6 GB
        mock_process.return_value.memory_info.return_value = mock_mem_info
        
        limit = 4.0  # 4 GB limit
        expected_usage_gb = 6.0
        
        with patch('utils.memory.get_config') as mock_cfg:
            mock_cfg.return_value.get_ram_limit.return_value = limit
            
            result = check_ram_usage(limit)
            
            self.assertTrue(result, "Should return True when limit exceeded")
            
            log_output = self.log_stream.getvalue()
            self.assertIn("RAM Warning", log_output)
            self.assertIn(f"{expected_usage_gb:.2f}", log_output)
            
            # Ensure no exception was raised
            self.assertTrue(True) 

    @patch('utils.memory.psutil.Process')
    def test_memory_watchdog_context_manager(self, mock_process):
        """
        Test the MemoryWatchdog context manager.
        """
        mock_mem_info = MagicMock()
        mock_mem_info.rss = 5 * (1024 ** 3)  # 5 GB
        mock_process.return_value.memory_info.return_value = mock_mem_info
        
        limit = 4.0
        
        with MemoryWatchdog(limit) as watchdog:
            # Inside context
            pass
        
        self.assertTrue(watchdog.peak_usage >= 5.0)
        self.assertIn("RAM Warning", self.log_stream.getvalue())


if __name__ == '__main__':
    import io
    unittest.main()