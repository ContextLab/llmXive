"""
Tests for the CPU-only execution guard module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cpu_guard import enforce_cpu_only, verify_no_cuda_usage, run_cpu_guard


class TestCPUGuard(unittest.TestCase):
    """Test cases for CPU guard functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Save original environment
        self.original_cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        # Reset environment for each test
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original environment
        if self.original_cuda_visible:
            os.environ["CUDA_VISIBLE_DEVICES"] = self.original_cuda_visible
        else:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)

    @patch('cpu_guard.torch')
    def test_enforce_cpu_only_sets_env_vars(self, mock_torch):
        """Test that enforce_cpu_only sets environment variables correctly."""
        enforce_cpu_only()
        
        self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "")
        mock_torch.cuda.is_available.assert_called()

    @patch('cpu_guard.torch')
    def test_enforce_cpu_only_disables_torch_cuda(self, mock_torch):
        """Test that enforce_cpu_only disables PyTorch CUDA if available."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        
        enforce_cpu_only()
        
        # Verify CUDA is disabled
        self.assertFalse(mock_torch.cuda.is_available())

    def test_verify_no_cuda_usage_with_empty_env(self):
        """Test verify_no_cuda_usage when CUDA_VISIBLE_DEVICES is empty."""
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        result = verify_no_cuda_usage()
        
        self.assertTrue(result)

    def test_verify_no_cuda_usage_with_set_env(self):
        """Test verify_no_cuda_usage when CUDA_VISIBLE_DEVICES is set."""
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        
        result = verify_no_cuda_usage()
        
        self.assertFalse(result)

    @patch('cpu_guard.torch')
    def test_verify_no_cuda_usage_with_torch_cuda_available(self, mock_torch):
        """Test verify_no_cuda_usage when PyTorch reports CUDA is available."""
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        mock_torch.cuda.is_available.return_value = True
        
        result = verify_no_cuda_usage()
        
        self.assertFalse(result)

    @patch('cpu_guard.torch')
    def test_verify_no_cuda_usage_with_torch_cuda_unavailable(self, mock_torch):
        """Test verify_no_cuda_usage when PyTorch reports CUDA is unavailable."""
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        mock_torch.cuda.is_available.return_value = False
        
        result = verify_no_cuda_usage()
        
        self.assertTrue(result)

    @patch('cpu_guard.torch')
    @patch('cpu_guard.verify_no_cuda_usage')
    def test_run_cpu_guard_success(self, mock_verify, mock_torch):
        """Test that run_cpu_guard succeeds when all checks pass."""
        mock_verify.return_value = True
        
        # Should not raise
        run_cpu_guard()
        
        mock_verify.assert_called_once()

    @patch('cpu_guard.torch')
    @patch('cpu_guard.verify_no_cuda_usage')
    def test_run_cpu_guard_failure(self, mock_verify, mock_torch):
        """Test that run_cpu_guard raises RuntimeError when checks fail."""
        mock_verify.return_value = False
        
        with self.assertRaises(RuntimeError):
            run_cpu_guard()


if __name__ == "__main__":
    unittest.main()