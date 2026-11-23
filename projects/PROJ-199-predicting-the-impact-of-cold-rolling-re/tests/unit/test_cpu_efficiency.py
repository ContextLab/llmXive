"""
Unit tests for CPU efficiency utilities.

These tests verify that GPU access is properly disabled and that
the CPU efficiency context manager works correctly.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure we can import from code/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.cpu_efficiency import (
    setup_cpu_efficiency,
    CPUOnlyContext,
    verify_no_gpu_access,
    main
)

class TestCPUEfficiency(unittest.TestCase):
    """Test cases for CPU efficiency utilities."""
    
    def setUp(self):
        """Save original environment variables before each test."""
        self._original_cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
        self._original_pytorch_no_cuda = os.environ.get("PYTORCH_NO_CUDA")
        self._original_omp = os.environ.get("OMP_NUM_THREADS")
        self._original_mkl = os.environ.get("MKL_NUM_THREADS")
        self._original_openblas = os.environ.get("OPENBLAS_NUM_THREADS")
        
    def tearDown(self):
        """Restore original environment variables after each test."""
        # Restore CUDA_VISIBLE_DEVICES
        if self._original_cuda_visible is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = self._original_cuda_visible
        elif "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
            
        # Restore PYTORCH_NO_CUDA
        if self._original_pytorch_no_cuda is not None:
            os.environ["PYTORCH_NO_CUDA"] = self._original_pytorch_no_cuda
        elif "PYTORCH_NO_CUDA" in os.environ:
            del os.environ["PYTORCH_NO_CUDA"]
            
        # Restore OMP_NUM_THREADS
        if self._original_omp is not None:
            os.environ["OMP_NUM_THREADS"] = self._original_omp
        elif "OMP_NUM_THREADS" in os.environ:
            del os.environ["OMP_NUM_THREADS"]
            
        # Restore MKL_NUM_THREADS
        if self._original_mkl is not None:
            os.environ["MKL_NUM_THREADS"] = self._original_mkl
        elif "MKL_NUM_THREADS" in os.environ:
            del os.environ["MKL_NUM_THREADS"]
            
        # Restore OPENBLAS_NUM_THREADS
        if self._original_openblas is not None:
            os.environ["OPENBLAS_NUM_THREADS"] = self._original_openblas
        elif "OPENBLAS_NUM_THREADS" in os.environ:
            del os.environ["OPENBLAS_NUM_THREADS"]
    
    def test_setup_cpu_efficiency_disables_gpu(self):
        """Test that setup_cpu_efficiency disables GPU access."""
        setup_cpu_efficiency()
        
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        self.assertEqual(os.environ.get("PYTORCH_NO_CUDA"), "1")
        
    def test_setup_cpu_efficiency_limits_threads(self):
        """Test that setup_cpu_efficiency limits thread pools."""
        setup_cpu_efficiency()
        
        self.assertEqual(os.environ.get("OMP_NUM_THREADS"), "1")
        self.assertEqual(os.environ.get("MKL_NUM_THREADS"), "1")
        self.assertEqual(os.environ.get("OPENBLAS_NUM_THREADS"), "1")
    
    def test_cpu_only_context_manager(self):
        """Test that CPUOnlyContext properly enforces and restores settings."""
        # Set original values
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        os.environ["PYTORCH_NO_CUDA"] = "0"
        
        with CPUOnlyContext():
            self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
            self.assertEqual(os.environ.get("PYTORCH_NO_CUDA"), "1")
        
        # Verify restoration
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "0")
        self.assertEqual(os.environ.get("PYTORCH_NO_CUDA"), "0")
    
    def test_cpu_only_context_manager_no_original(self):
        """Test CPUOnlyContext when no original values exist."""
        # Ensure no original values
        if "CUDA_VISIBLE_DEVICES" in os.environ:
            del os.environ["CUDA_VISIBLE_DEVICES"]
        if "PYTORCH_NO_CUDA" in os.environ:
            del os.environ["PYTORCH_NO_CUDA"]
        
        with CPUOnlyContext():
            self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
            self.assertEqual(os.environ.get("PYTORCH_NO_CUDA"), "1")
        
        # Verify removal after context
        self.assertNotIn("CUDA_VISIBLE_DEVICES", os.environ)
        self.assertNotIn("PYTORCH_NO_CUDA", os.environ)
    
    @patch("utils.cpu_efficiency.os.environ")
    @patch("utils.cpu_efficiency.torch")
    def test_verify_no_gpu_access_with_pytorch(self, mock_torch, mock_environ):
        """Test verify_no_gpu_access when PyTorch reports CUDA available."""
        mock_torch.cuda.is_available.return_value = True
        mock_environ.get.return_value = ""
        
        result = verify_no_gpu_access()
        
        self.assertFalse(result)
        
    @patch("utils.cpu_efficiency.os.environ")
    @patch("utils.cpu_efficiency.torch")
    def test_verify_no_gpu_access_clean(self, mock_torch, mock_environ):
        """Test verify_no_gpu_access when no GPU is available."""
        mock_torch.cuda.is_available.return_value = False
        mock_environ.get.return_value = ""
        
        result = verify_no_gpu_access()
        
        self.assertTrue(result)
    
    @patch("utils.cpu_efficiency.os.environ")
    def test_verify_no_gpu_access_cuda_visible_set(self, mock_environ):
        """Test verify_no_gpu_access when CUDA_VISIBLE_DEVICES is set."""
        mock_environ.get.return_value = "0"
        
        result = verify_no_gpu_access()
        
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
