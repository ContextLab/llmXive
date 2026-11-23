"""
Tests for the CPU-only environment verification module.
"""

import sys
import unittest
from unittest.mock import patch
import torch

# Import the module under test
from src.lib.check_cpu import verify_cpu_only, GPUEnvironmentError


class TestCPUCheck(unittest.TestCase):
    """Test cases for CPU verification logic."""

    @patch('src.lib.check_cpu.torch.cuda.is_available', return_value=False)
    @patch('src.lib.check_cpu.torch.cuda.device_count', return_value=0)
    def test_cpu_only_success(self, mock_device_count, mock_is_available):
        """
        Test that verify_cpu_only passes silently when no GPU is available.
        """
        # Should not raise any exception
        try:
            verify_cpu_only()
        except GPUEnvironmentError:
            self.fail("verify_cpu_only() raised GPUEnvironmentError unexpectedly when no GPU is present.")

    @patch('src.lib.check_cpu.torch.cuda.is_available', return_value=True)
    @patch('src.lib.check_cpu.torch.cuda.device_count', return_value=1)
    @patch('src.lib.check_cpu.torch.cuda.get_device_properties')
    def test_gpu_detected_raises_error(self, mock_get_props, mock_device_count, mock_is_available):
        """
        Test that verify_cpu_only raises GPUEnvironmentError when a GPU is detected.
        """
        # Mock the device properties
        mock_props = unittest.mock.MagicMock()
        mock_props.name = "Test GPU"
        mock_get_props.return_value = mock_props

        with self.assertRaises(GPUEnvironmentError) as context:
            verify_cpu_only()

        self.assertIn("GPU detected", str(context.exception))
        self.assertIn("CPU-only", str(context.exception))

    @patch('src.lib.check_cpu.torch.cuda.is_available', return_value=True)
    @patch('src.lib.check_cpu.torch.cuda.device_count', return_value=2)
    @patch('src.lib.check_cpu.torch.cuda.get_device_properties')
    def test_gpu_detected_multiple_devices(self, mock_get_props, mock_device_count, mock_is_available):
        """
        Test that verify_cpu_only correctly reports multiple GPUs.
        """
        # Mock properties for two devices
        def get_props_side_effect(i):
            mock_props = unittest.mock.MagicMock()
            mock_props.name = f"GPU-{i}"
            return mock_props

        mock_get_props.side_effect = get_props_side_effect

        with self.assertRaises(GPUEnvironmentError) as context:
            verify_cpu_only()

        self.assertIn("2 CUDA device(s)", str(context.exception))


if __name__ == '__main__':
    unittest.main()