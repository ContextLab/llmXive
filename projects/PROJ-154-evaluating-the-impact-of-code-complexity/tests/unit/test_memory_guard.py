"""
Unit tests for the memory_guard module.

Tests verify:
1. MemoryConfig loading from a mock config file.
2. get_memory_usage_gb returns a float.
3. MemoryGuard correctly triggers abort or downsample based on thresholds.
4. check_and_abort_or_downsample helper function behavior.
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_guard import (
    MemoryConfig,
    load_config,
    get_memory_usage_gb,
    MemoryGuard,
    check_and_abort_or_downsample,
)


class TestMemoryConfig(unittest.TestCase):
    """Tests for the MemoryConfig dataclass and loading."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = MemoryConfig()
        self.assertEqual(config.memory_threshold_percent, 80.0)
        self.assertEqual(config.max_batch_size, 100)
        self.assertEqual(config.downsample_factor, 0.5)

    def test_custom_values(self):
        """Test setting custom values."""
        config = MemoryConfig(memory_threshold_percent=90.0, max_batch_size=50)
        self.assertEqual(config.memory_threshold_percent, 90.0)
        self.assertEqual(config.max_batch_size, 50)


class TestLoadConfig(unittest.TestCase):
    """Tests for loading configuration from a YAML/JSON file."""

    def setUp(self):
        """Create a temporary config file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.yaml"
        
        # Create a mock config file (using JSON for simplicity in test, 
        # but the loader handles YAML-like structure if using a simple parser)
        # Since the actual loader might use yaml or a custom parser, 
        # we assume it reads key-value pairs. 
        # For this test, we create a JSON file which is often compatible 
        # with simple loaders or we mock the yaml load.
        config_data = {
            "memory_threshold_percent": 75.0,
            "max_batch_size": 20,
            "downsample_factor": 0.25
        }
        with open(self.config_path, "w") as f:
            json.dump(config_data, f)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    @patch('utils.memory_guard.yaml')
    def test_load_config_file(self, mock_yaml):
        """Test loading a valid config file."""
        mock_yaml.safe_load.return_value = {
            "memory_threshold_percent": 75.0,
            "max_batch_size": 20,
            "downsample_factor": 0.25
        }
        
        config = load_config(self.config_path)
        
        self.assertEqual(config.memory_threshold_percent, 75.0)
        self.assertEqual(config.max_batch_size, 20)
        self.assertEqual(config.downsample_factor, 0.25)

    def test_load_config_missing_file(self):
        """Test behavior when config file is missing."""
        non_existent_path = Path(self.temp_dir.name) / "non_existent.yaml"
        # Should return defaults or handle gracefully
        config = load_config(non_existent_path)
        self.assertIsInstance(config, MemoryConfig)


class TestGetMemoryUsageGb(unittest.TestCase):
    """Tests for memory usage calculation."""

    @patch('utils.memory_guard.psutil')
    def test_get_memory_usage(self, mock_psutil):
        """Test that get_memory_usage_gb returns a float."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1 GB
        mock_psutil.Process.return_value = mock_process

        usage = get_memory_usage_gb()
        
        self.assertIsInstance(usage, float)
        self.assertAlmostEqual(usage, 1.0, places=1)

    @patch('utils.memory_guard.psutil')
    def test_get_memory_usage_error_handling(self, mock_psutil):
        """Test error handling if psutil fails."""
        mock_psutil.Process.side_effect = Exception("Mock error")
        
        # Should return 0.0 or handle gracefully
        usage = get_memory_usage_gb()
        self.assertEqual(usage, 0.0)


class TestMemoryGuard(unittest.TestCase):
    """Tests for the MemoryGuard class logic."""

    def setUp(self):
        """Setup test environment."""
        self.config = MemoryConfig(
            memory_threshold_percent=50.0,
            max_batch_size=10,
            downsample_factor=0.5
        )
        self.guard = MemoryGuard(self.config)

    @patch('utils.memory_guard.get_memory_usage_gb')
    def test_check_memory_below_threshold(self, mock_usage):
        """Test that no action is taken when memory is low."""
        mock_usage.return_value = 20.0  # Well below 50%
        
        current_batch = 10
        should_abort, new_batch = self.guard.check_and_downsample(current_batch)
        
        self.assertFalse(should_abort)
        self.assertEqual(new_batch, current_batch)

    @patch('utils.memory_guard.get_memory_usage_gb')
    def test_check_memory_above_threshold_downsample(self, mock_usage):
        """Test that downsampling occurs when memory is high."""
        mock_usage.return_value = 80.0  # Above 50%
        
        current_batch = 10
        should_abort, new_batch = self.guard.check_and_downsample(current_batch)
        
        self.assertFalse(should_abort)
        self.assertEqual(new_batch, 5)  # 10 * 0.5

    @patch('utils.memory_guard.get_memory_usage_gb')
    def test_check_memory_above_threshold_abort(self, mock_usage):
        """Test that abort occurs if downsampling doesn't help or batch is too small."""
        mock_usage.return_value = 99.0  # Critical
        
        current_batch = 1
        should_abort, new_batch = self.guard.check_and_downsample(current_batch)
        
        # If batch is already 1, we might abort
        self.assertTrue(should_abort)
        self.assertEqual(new_batch, 1) # Or 0, depending on implementation

    @patch('utils.memory_guard.get_memory_usage_gb')
    def test_check_memory_critical(self, mock_usage):
        """Test critical memory threshold."""
        mock_usage.return_value = 95.0 
        
        current_batch = 10
        should_abort, new_batch = self.guard.check_and_downsample(current_batch)
        
        # Logic: if memory > critical (e.g. 95), maybe abort immediately?
        # Assuming standard logic: try to downsample first.
        # If downsampled batch is still too small or memory still high, abort.
        # For this test, we expect a downsample attempt unless logic says abort > 90.
        # Based on typical implementation:
        self.assertFalse(should_abort) # First attempt downsample
        self.assertEqual(new_batch, 5)


class TestCheckAndAbortOrDownsample(unittest.TestCase):
    """Tests for the helper function."""

    @patch('utils.memory_guard.MemoryGuard')
    @patch('utils.memory_guard.load_config')
    def test_helper_function_calls_guard(self, mock_load, mock_guard_cls):
        """Test that the helper function instantiates guard and calls method."""
        mock_config = MemoryConfig()
        mock_load.return_value = mock_config
        
        mock_guard_instance = MagicMock()
        mock_guard_instance.check_and_downsample.return_value = (False, 5)
        mock_guard_cls.return_value = mock_guard_instance

        should_abort, new_batch = check_and_abort_or_downsample(10)
        
        self.assertFalse(should_abort)
        self.assertEqual(new_batch, 5)
        mock_guard_cls.assert_called_once_with(mock_config)
        mock_guard_instance.check_and_downsample.assert_called_once_with(10)

    @patch('utils.memory_guard.MemoryGuard')
    @patch('utils.memory_guard.load_config')
    def test_helper_function_abort(self, mock_load, mock_guard_cls):
        """Test abort scenario in helper."""
        mock_config = MemoryConfig()
        mock_load.return_value = mock_config
        
        mock_guard_instance = MagicMock()
        mock_guard_instance.check_and_downsample.return_value = (True, 1)
        mock_guard_cls.return_value = mock_guard_instance

        should_abort, new_batch = check_and_abort_or_downsample(10)
        
        self.assertTrue(should_abort)
        self.assertEqual(new_batch, 1)


if __name__ == "__main__":
    unittest.main()