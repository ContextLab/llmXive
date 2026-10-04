"""
Tests for the CPU environment verification module.
"""

import sys
import unittest
from unittest.mock import patch

import torch

# Import the module under test
# The path is relative to the project root where 'code' is the root of the python package
# Assuming tests are run with PYTHONPATH set to include 'code'
from src.lib.check_cpu import verify_cpu_only, GPUEnvironmentError


class TestCPUCheck(unittest.TestCase):
    """Test cases for verify_cpu_only function."""

    def test_cpu_only_success(self):
        """
        Test that verify_cpu_only passes when no GPU is available.
        """
        with patch('torch.cuda.is_available', return_value=False):
            # Should not raise any exception
            try:
                verify_cpu_only()
            except GPUEnvironmentError:
                self.fail("verify_cpu_only() raised GPUEnvironmentError unexpectedly when no GPU is available.")

    def test_gpu_detected_raises_error(self):
        """
        Test that verify_cpu_only raises GPUEnvironmentError when a GPU is available.
        """
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.device_count', return_value=1):
                with patch('torch.cuda.get_device_name', return_value="NVIDIA Tesla T4"):
                    with self.assertRaises(GPUEnvironmentError) as context:
                        verify_cpu_only()

                    self.assertIn("GPU environment detected", str(context.exception))
                    self.assertIn("NVIDIA Tesla T4", str(context.exception))

    def test_gpu_detected_no_device_name(self):
        """
        Test error message handling when device count is 0 but is_available is True (edge case).
        """
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.device_count', return_value=0):
                with patch('torch.cuda.get_device_name', side_effect=AssertionError("No device")):
                    with self.assertRaises(GPUEnvironmentError) as context:
                        verify_cpu_only()
                    # Ensure it still raises, even if name retrieval fails (though unlikely in real torch)
                    self.assertIn("GPU environment detected", str(context.exception))

if __name__ == '__main__':
    unittest.main()