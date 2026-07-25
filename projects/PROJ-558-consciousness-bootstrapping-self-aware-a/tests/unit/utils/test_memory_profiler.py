import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import resource

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.memory_profiler import get_current_memory_mb, get_peak_memory_mb, profile_training_script

class TestMemoryProfiler(unittest.TestCase):

    def test_get_current_memory_mb(self):
        """Test that get_current_memory_mb returns a positive float."""
        mem = get_current_memory_mb()
        self.assertIsInstance(mem, float)
        self.assertGreater(mem, 0)

    def test_get_peak_memory_mb(self):
        """Test that get_peak_memory_mb returns a positive float."""
        mem = get_peak_memory_mb()
        self.assertIsInstance(mem, float)
        self.assertGreater(mem, 0)

    @patch('utils.memory_profiler.resource.getrusage')
    def test_memory_calculation(self, mock_getrusage):
        """Test memory calculation with mocked resource."""
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 102400  # 100 MB in KB
        mock_getrusage.return_value = mock_usage

        mem_mb = get_current_memory_mb()
        self.assertEqual(mem_mb, 100.0)

    @patch('utils.memory_profiler.get_current_memory_mb')
    @patch('utils.memory_profiler.get_peak_memory_mb')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('os.makedirs')
    def test_profile_training_script_success(self, mock_makedirs, mock_open, mock_peak, mock_current):
        """Test successful profiling run."""
        mock_current.return_value = 100.0
        mock_peak.return_value = 5000.0  # ~5 GB

        script_path = "code/training/train.py"
        output_path = "artifacts/results/memory_profile.log"
        max_batch_size = 4
        max_limit = 7.0

        # Mock the exec to not raise
        with patch('builtins.exec'):
            result = profile_training_script(
                script_path=script_path,
                max_batch_size=max_batch_size,
                output_log_path=output_path,
                max_memory_limit_gb=max_limit
            )

        self.assertTrue(result["success"])
        self.assertTrue(result["passed_limit"])
        self.assertEqual(result["peak_memory_mb"], 5000.0)
        self.assertEqual(result["peak_memory_gb"], 5000.0 / 1024.0)
        mock_open.assert_called_once_with(output_path, 'w')

    @patch('utils.memory_profiler.get_current_memory_mb')
    @patch('utils.memory_profiler.get_peak_memory_mb')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('os.makedirs')
    def test_profile_training_script_exceeds_limit(self, mock_makedirs, mock_open, mock_peak, mock_current):
        """Test profiling when memory exceeds limit."""
        mock_current.return_value = 100.0
        mock_peak.return_value = 8000.0  # ~7.8 GB

        script_path = "code/training/train.py"
        output_path = "artifacts/results/memory_profile.log"
        max_batch_size = 4
        max_limit = 7.0

        with patch('builtins.exec'):
            result = profile_training_script(
                script_path=script_path,
                max_batch_size=max_batch_size,
                output_log_path=output_path,
                max_memory_limit_gb=max_limit
            )

        self.assertTrue(result["success"])
        self.assertFalse(result["passed_limit"])
        self.assertGreater(result["peak_memory_gb"], 7.0)

    @patch('utils.memory_profiler.get_current_memory_mb')
    @patch('utils.memory_profiler.get_peak_memory_mb')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('os.makedirs')
    def test_profile_training_script_error(self, mock_makedirs, mock_open, mock_peak, mock_current):
        """Test profiling when script raises an error."""
        mock_current.return_value = 100.0
        mock_peak.return_value = 2000.0

        script_path = "code/training/train.py"
        output_path = "artifacts/results/memory_profile.log"
        max_batch_size = 4
        max_limit = 7.0

        with patch('builtins.exec', side_effect=Exception("Test error")):
            result = profile_training_script(
                script_path=script_path,
                max_batch_size=max_batch_size,
                output_log_path=output_path,
                max_memory_limit_gb=max_limit
            )

        self.assertFalse(result["success"])
        self.assertIn("Test error", result["error"])
        self.assertFalse(result["passed_limit"])

if __name__ == "__main__":
    unittest.main()
