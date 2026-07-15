"""
Tests for CPU-only execution guard functionality.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from cpu_guard import enforce_cpu_only, verify_no_cuda_usage, run_cpu_guard


class TestCPUGuard(unittest.TestCase):
    """Test cases for CPU guard functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Save original environment
        self.original_env = os.environ.copy()
        # Reset environment for each test
        os.environ.clear()
        os.environ.update(self.original_env)

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('cpu_guard.logger')
    def test_enforce_cpu_only_sets_env_vars(self, mock_logger):
        """Test that enforce_cpu_only sets the correct environment variables."""
        enforce_cpu_only()
        
        # Check that CUDA_VISIBLE_DEVICES is set to empty string
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        # Check that TORCH_USE_CPU_ONLY is set
        self.assertEqual(os.environ.get("TORCH_USE_CPU_ONLY"), "1")
        
        # Verify logger was called
        mock_logger.info.assert_called()

    @patch('cpu_guard.logger')
    def test_verify_no_cuda_usage_without_torch(self, mock_logger):
        """Test verify_no_cuda_usage when torch is not installed."""
        # Mock ImportError for torch
        with patch.dict('sys.modules', {'torch': None}):
            with patch('cpu_guard.importlib.import_module', side_effect=ImportError):
                result = verify_no_cuda_usage()
                self.assertTrue(result)

    @patch('cpu_guard.logger')
    def test_verify_no_cuda_usage_with_torch_cpu_only(self, mock_logger):
        """Test verify_no_cuda_usage when torch is available but CPU-only."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.device_count.return_value = 0
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            result = verify_no_cuda_usage()
            self.assertTrue(result)

    @patch('cpu_guard.logger')
    def test_verify_no_cuda_usage_fails_with_cuda(self, mock_logger):
        """Test verify_no_cuda_usage fails when CUDA is available and in use."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            result = verify_no_cuda_usage()
            self.assertFalse(result)

    @patch('cpu_guard.logger')
    def test_run_cpu_guard_success(self, mock_logger):
        """Test run_cpu_guard when everything passes."""
        # Mock the dependencies to succeed
        with patch('cpu_guard.enforce_cpu_only'):
            with patch('cpu_guard.verify_no_cuda_usage', return_value=True):
                with patch.dict('sys.modules', {
                    'radon': MagicMock(),
                    'pylint': MagicMock()
                }):
                    result = run_cpu_guard()
                    self.assertTrue(result)

    @patch('cpu_guard.logger')
    def test_run_cpu_guard_fails_cuda_check(self, mock_logger):
        """Test run_cpu_guard fails when CUDA check fails."""
        with patch('cpu_guard.enforce_cpu_only'):
            with patch('cpu_guard.verify_no_cuda_usage', return_value=False):
                result = run_cpu_guard()
                self.assertFalse(result)

    @patch('cpu_guard.logger')
    def test_run_cpu_guard_fails_radon_import(self, mock_logger):
        """Test run_cpu_guard fails when radon cannot be imported."""
        with patch('cpu_guard.enforce_cpu_only'):
            with patch('cpu_guard.verify_no_cuda_usage', return_value=True):
                with patch.dict('sys.modules', {
                    'radon': None,
                    'pylint': MagicMock()
                }):
                    # Simulate ImportError for radon
                    original_import = __builtins__.__import__
                    def mock_import(name, *args, **kwargs):
                        if name == 'radon':
                            raise ImportError("radon not found")
                        return original_import(name, *args, **kwargs)
                    
                    with patch.object(__builtins__, '__import__', side_effect=mock_import):
                        result = run_cpu_guard()
                        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
