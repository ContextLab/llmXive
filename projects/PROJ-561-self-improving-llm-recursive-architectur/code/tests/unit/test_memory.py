import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import psutil
from utils.memory import check_and_terminate_if_exceeds, get_memory_usage_gb, enable_gradient_checkpointing

class TestMemoryWatchdog(unittest.TestCase):
    @patch('utils.memory.psutil.Process')
    def test_check_and_terminate_if_exceeds(self, mock_process):
        mock_process.return_value.memory_info.return_value.rss = 1024 ** 4  # 1GB
        # Should not terminate
        check_and_terminate_if_exceeds(2.0)

    @patch('utils.memory.psutil.Process')
    def test_check_and_terminate_if_exceeds_fail(self, mock_process):
        mock_process.return_value.memory_info.return_value.rss = 1024 ** 4 * 10 # 10GB
        with self.assertRaises(SystemExit):
            check_and_terminate_if_exceeds(2.0)

class TestGradientCheckpointing(unittest.TestCase):
    def test_enable_gradient_checkpointing(self):
        class MockModel:
            def gradient_checkpointing_enable(self):
                pass
        model = MockModel()
        enable_gradient_checkpointing(model) # Should not raise

if __name__ == '__main__':
    unittest.main()