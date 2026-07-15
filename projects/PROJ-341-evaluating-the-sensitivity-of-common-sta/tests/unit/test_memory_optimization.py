import unittest
import os
import sys
import gc
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.main import get_memory_usage_mb, check_memory_limit, CHUNK_SIZE, MAX_MEMORY_GB

class TestMemoryOptimization(unittest.TestCase):

    def test_get_memory_usage_mb(self):
        """Test that memory usage function returns a positive number."""
        mem = get_memory_usage_mb()
        self.assertGreater(mem, 0)

    @patch('code.main.psutil.Process')
    def test_check_memory_limit_no_gc(self, mock_process):
        """Test that GC is not triggered when memory is below limit."""
        # Mock memory usage to be low
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        
        with patch('code.main.gc.collect') as mock_gc:
            check_memory_limit()
            mock_gc.assert_not_called()

    @patch('code.main.psutil.Process')
    def test_check_memory_limit_triggers_gc(self, mock_process):
        """Test that GC is triggered when memory exceeds limit."""
        # Mock memory usage to be high (e.g., 8GB)
        mock_process.return_value.memory_info.return_value.rss = 8 * 1024 * 1024 * 1024
        
        with patch('code.main.gc.collect') as mock_gc:
            with patch('code.main.logger') as mock_logger:
                check_memory_limit()
                mock_gc.assert_called_once()
                mock_logger.warning.assert_called()

    def test_chunk_size_definition(self):
        """Verify CHUNK_SIZE is defined and reasonable."""
        self.assertIsInstance(CHUNK_SIZE, int)
        self.assertGreater(CHUNK_SIZE, 0)
        self.assertLessEqual(CHUNK_SIZE, 10000)  # Reasonable upper bound

    def test_max_memory_gb_definition(self):
        """Verify MAX_MEMORY_GB is defined and below 7GB."""
        self.assertIsInstance(MAX_MEMORY_GB, (int, float))
        self.assertLess(MAX_MEMORY_GB, 7.0)
        self.assertGreater(MAX_MEMORY_GB, 1.0)

if __name__ == '__main__':
    unittest.main()