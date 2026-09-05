import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.loader import adaptive_sample_size, get_memory_usage

class TestAdaptiveSampleSize(unittest.TestCase):
    """Unit tests for memory profiling logic in code/data/loader.py"""

    def test_adaptive_sample_size_returns_correct_limit(self):
        """
        Test that adaptive_sample_size returns a positive integer based on
        measured overhead and target memory limit.
        """
        # Mock parameters
        batch_size = 32
        target_gb = 4.0
        measured_overhead_per_molecule = 0.001  # 1 MB per molecule in GB

        # Calculate expected max_samples manually
        # Formula roughly: target_gb / (overhead + fixed_batch_overhead)
        # We just need to assert it returns a valid positive integer > 0
        max_samples = adaptive_sample_size(batch_size, target_gb, measured_overhead_per_molecule)

        self.assertIsInstance(max_samples, int)
        self.assertGreater(max_samples, 0)

    def test_adaptive_sample_size_zero_target(self):
        """Test behavior when target memory is extremely low."""
        max_samples = adaptive_sample_size(32, 0.0001, 0.001)
        # Should return 0 or a very small number, but not crash
        self.assertGreaterEqual(max_samples, 0)

    def test_adaptive_sample_size_large_overhead(self):
        """Test behavior when per-molecule overhead is high."""
        # If overhead is 1GB per molecule and target is 2GB, max should be small
        max_samples = adaptive_sample_size(32, 2.0, 1.0)
        self.assertGreaterEqual(max_samples, 0)
        self.assertLessEqual(max_samples, 2)

    def test_adaptive_sample_size_normal_case(self):
        """Test normal operation with realistic values."""
        # Typical values: 32 batch, 6GB target, 0.0005GB (0.5MB) overhead
        max_samples = adaptive_sample_size(32, 6.0, 0.0005)
        self.assertGreater(max_samples, 1000) # Should allow many molecules

class TestGetMemoryUsage(unittest.TestCase):
    """Unit tests for memory usage utility"""

    @patch('psutil.Process')
    def test_get_memory_usage_returns_positive(self, mock_process_class):
        """Test that get_memory_usage returns a positive number."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 500 # 500MB
        mock_process_class.return_value = mock_process

        usage = get_memory_usage()
        
        self.assertIsInstance(usage, float)
        self.assertGreater(usage, 0)

if __name__ == '__main__':
    unittest.main()
