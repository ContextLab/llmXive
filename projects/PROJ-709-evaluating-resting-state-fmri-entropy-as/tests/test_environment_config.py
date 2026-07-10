"""
Tests for environment configuration management.

These tests verify that CPU-only configuration is correctly applied
and that the environment validation functions work as expected.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from environment_config import (
    configure_cpu_only,
    get_environment_summary,
    validate_cpu_only,
    main
)


class TestEnvironmentConfig(unittest.TestCase):
    """Test cases for environment configuration functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset environment variables before each test
        self.original_env = os.environ.copy()
        logging.basicConfig(level=logging.WARNING)

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_configure_cpu_only_sets_cuda_visible_devices(self):
        """Test that CUDA_VISIBLE_DEVICES is set to empty string."""
        result = configure_cpu_only()
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "")
        self.assertTrue(result["cuda_disabled"])

    def test_configure_cpu_only_sets_thread_limits(self):
        """Test that thread limits are set correctly."""
        result = configure_cpu_only()
        self.assertEqual(os.environ.get("OMP_NUM_THREADS"), "1")
        self.assertEqual(os.environ.get("MKL_NUM_THREADS"), "1")
        self.assertEqual(os.environ.get("OPENBLAS_NUM_THREADS"), "1")
        self.assertTrue(result["openmp_threads_set"])
        self.assertTrue(result["numpy_threads_set"])

    def test_configure_cpu_only_returns_status_dict(self):
        """Test that configure_cpu_only returns a dictionary with expected keys."""
        result = configure_cpu_only()
        expected_keys = [
            "cuda_disabled",
            "torch_cpu_only",
            "tensorflow_cpu_only",
            "openmp_threads_set",
            "numpy_threads_set",
        ]
        for key in expected_keys:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], bool)

    def test_get_environment_summary_contains_expected_keys(self):
        """Test that get_environment_summary returns a dictionary with expected keys."""
        summary = get_environment_summary()
        expected_keys = [
            "cuda_visible_devices",
            "cuda_device_order",
            "omp_num_threads",
            "platform",
            "python_version",
            "torch_available",
            "tensorflow_available",
            "numpy_available",
            "scipy_available",
        ]
        for key in expected_keys:
            self.assertIn(key, summary)

    def test_get_environment_summary_includes_library_versions(self):
        """Test that library versions are included when libraries are available."""
        summary = get_environment_summary()

        # Check if NumPy is available and its version is recorded
        if summary.get("numpy_available", False):
            self.assertIn("numpy_version", summary)
            self.assertIsNotNone(summary["numpy_version"])

    def test_validate_cpu_only_returns_boolean(self):
        """Test that validate_cpu_only returns a boolean value."""
        # Configure first to ensure environment is set up
        configure_cpu_only()
        result = validate_cpu_only()
        self.assertIsInstance(result, bool)

    def test_main_function_executes_without_error(self):
        """Test that main() executes without raising exceptions."""
        # Mock sys.exit to capture the return code
        with patch("sys.exit") as mock_exit:
            main()
            mock_exit.assert_called_once()
            # The return code should be 0 (success) or 1 (failure)
            self.assertIn(mock_exit.call_args[0][0], [0, 1])

    @patch("environment_config.import torch")
    def test_configure_cpu_only_handles_missing_torch(self, mock_import):
        """Test that configure_cpu_only handles missing PyTorch gracefully."""
        mock_import.side_effect = ImportError("No module named 'torch'")
        result = configure_cpu_only()
        # Should not raise an exception
        self.assertTrue(result["cuda_disabled"])

    @patch("environment_config.import tensorflow")
    def test_configure_cpu_only_handles_missing_tensorflow(self, mock_import):
        """Test that configure_cpu_only handles missing TensorFlow gracefully."""
        mock_import.side_effect = ImportError("No module named 'tensorflow'")
        result = configure_cpu_only()
        # Should not raise an exception
        self.assertTrue(result["cuda_disabled"])


if __name__ == "__main__":
    unittest.main()
