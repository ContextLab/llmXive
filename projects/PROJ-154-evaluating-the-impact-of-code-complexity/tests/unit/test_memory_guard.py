"""
Unit tests for memory_guard.py
Tests for MemoryConfig, load_config, get_memory_usage_gb, check_and_abort_or_downsample, and MemoryGuard.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from dataclasses import dataclass
from typing import List, Any, Callable, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.memory_guard import (
    MemoryConfig,
    load_config,
    get_memory_usage_gb,
    check_and_abort_or_downsample,
    MemoryGuard
)

class TestMemoryConfig(unittest.TestCase):
    """Tests for MemoryConfig dataclass"""

    def test_memory_config_creation(self):
        """Test that MemoryConfig can be created with default values"""
        config = MemoryConfig()
        self.assertEqual(config.threshold_percent, 80.0)
        self.assertEqual(config.initial_batch_size, 10)
        self.assertEqual(config.min_batch_size, 1)
        self.assertIsNotNone(config.rms_memory_gb)

    def test_memory_config_custom_values(self):
        """Test MemoryConfig with custom values"""
        config = MemoryConfig(
            threshold_percent=75.0,
            initial_batch_size=20,
            min_batch_size=2
        )
        self.assertEqual(config.threshold_percent, 75.0)
        self.assertEqual(config.initial_batch_size, 20)
        self.assertEqual(config.min_batch_size, 2)

class TestLoadConfig(unittest.TestCase):
    """Tests for load_config function"""

    def setUp(self):
        """Set up temporary directory for config files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.yaml")

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_load_config_from_file(self):
        """Test loading config from a valid YAML file"""
        config_content = """
        memory_threshold_percent: 75.0
        initial_batch_size: 5
        min_batch_size: 1
        """
        with open(self.config_path, 'w') as f:
            f.write(config_content)

        config = load_config(self.config_path)
        self.assertEqual(config.threshold_percent, 75.0)
        self.assertEqual(config.initial_batch_size, 5)
        self.assertEqual(config.min_batch_size, 1)

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_default_values(self):
        """Test that load_config uses defaults for missing keys"""
        config_content = """
        memory_threshold_percent: 85.0
        """
        with open(self.config_path, 'w') as f:
            f.write(config_content)

        config = load_config(self.config_path)
        self.assertEqual(config.threshold_percent, 85.0)
        self.assertEqual(config.initial_batch_size, 10)  # default
        self.assertEqual(config.min_batch_size, 1)  # default

class TestGetMemoryUsageGb(unittest.TestCase):
    """Tests for get_memory_usage_gb function"""

    def test_get_memory_usage_returns_positive(self):
        """Test that get_memory_usage_gb returns a positive number"""
        usage = get_memory_usage_gb()
        self.assertGreater(usage, 0)
        self.assertIsInstance(usage, float)

    @patch('utils.memory_guard.psutil')
    def test_get_memory_usage_with_mock(self, mock_psutil):
        """Test get_memory_usage_gb with mocked psutil"""
        mock_memory = MagicMock()
        mock_memory.percent = 50.0
        mock_memory.used = 4 * 1024 * 1024 * 1024  # 4 GB
        mock_psutil.virtual_memory.return_value = mock_memory

        usage = get_memory_usage_gb()
        
        # Should be around 4.0 GB (with some tolerance for measurement)
        self.assertGreater(usage, 3.5)
        self.assertLess(usage, 4.5)

class TestCheckAndAbortOrDownsample(unittest.TestCase):
    """Tests for check_and_abort_or_downsample function"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = MemoryConfig(
            threshold_percent=80.0,
            initial_batch_size=10,
            min_batch_size=2
        )
        self.batch_sizes: List[int] = []

    def test_check_below_threshold_no_action(self):
        """Test that no action is taken when memory is below threshold"""
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=50.0):
            result = check_and_abort_or_downsample(
                self.config,
                current_batch_size=10,
                batch_sizes=self.batch_sizes
            )
            self.assertEqual(result, 10)  # No change
            self.assertEqual(len(self.batch_sizes), 0)  # No downsample recorded

    def test_check_above_threshold_downsample(self):
        """Test that downsampling occurs when memory exceeds threshold"""
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            result = check_and_abort_or_downsample(
                self.config,
                current_batch_size=10,
                batch_sizes=self.batch_sizes
            )
            self.assertEqual(result, 5)  # Batch size halved
            self.assertEqual(len(self.batch_sizes), 1)
            self.assertEqual(self.batch_sizes[0], 5)

    def test_check_above_threshold_min_batch_size(self):
        """Test that abort occurs when batch size would go below minimum"""
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            result = check_and_abort_or_downsample(
                self.config,
                current_batch_size=2,
                batch_sizes=self.batch_sizes
            )
            # Should raise SystemExit because min_batch_size is 2
            with self.assertRaises(SystemExit) as context:
                check_and_abort_or_downsample(
                    self.config,
                    current_batch_size=2,
                    batch_sizes=self.batch_sizes
                )
            self.assertIn("Memory usage exceeds threshold", str(context.exception))

    def test_check_multiple_downsamples(self):
        """Test multiple downsampling iterations"""
        # First call: 85% usage, batch 10 -> 5
        # Second call: 85% usage, batch 5 -> 2 (but min is 2, so next would abort)
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            result1 = check_and_abort_or_downsample(
                self.config,
                current_batch_size=10,
                batch_sizes=self.batch_sizes
            )
            self.assertEqual(result1, 5)
            self.assertEqual(len(self.batch_sizes), 1)

            result2 = check_and_abort_or_downsample(
                self.config,
                current_batch_size=5,
                batch_sizes=self.batch_sizes
            )
            self.assertEqual(result2, 2)
            self.assertEqual(len(self.batch_sizes), 2)

    def test_check_with_custom_min_batch_size(self):
        """Test downsampling with custom minimum batch size"""
        custom_config = MemoryConfig(
            threshold_percent=80.0,
            initial_batch_size=10,
            min_batch_size=3
        )
        
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            result = check_and_abort_or_downsample(
                custom_config,
                current_batch_size=4,
                batch_sizes=self.batch_sizes
            )
            # 4 -> 2, but 2 < min_batch_size (3), so should abort
            with self.assertRaises(SystemExit):
                check_and_abort_or_downsample(
                    custom_config,
                    current_batch_size=4,
                    batch_sizes=self.batch_sizes
                )

class TestMemoryGuard(unittest.TestCase):
    """Tests for MemoryGuard class"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = MemoryConfig(
            threshold_percent=80.0,
            initial_batch_size=10,
            min_batch_size=2
        )
        
        # Create a sample batch of items
        self.sample_batch = [f"item_{i}" for i in range(10)]

    def test_memory_guard_initialization(self):
        """Test MemoryGuard initialization"""
        guard = MemoryGuard(self.config)
        self.assertEqual(guard.config.threshold_percent, 80.0)
        self.assertEqual(guard.current_batch_size, 10)
        self.assertGreater(guard.initial_memory_gb, 0)

    def test_memory_guard_process_batch_below_threshold(self):
        """Test processing a batch when memory is below threshold"""
        guard = MemoryGuard(self.config)
        
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=50.0):
            result = guard.process_batch(self.sample_batch)
            self.assertEqual(len(result), 10)  # Full batch processed
            self.assertEqual(guard.current_batch_size, 10)
            self.assertEqual(len(guard.batch_sizes), 0)

    def test_memory_guard_process_batch_above_threshold(self):
        """Test processing a batch when memory exceeds threshold"""
        guard = MemoryGuard(self.config)
        
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            result = guard.process_batch(self.sample_batch)
            # Should process smaller batch after downsampling
            self.assertLess(len(result), 10)
            self.assertGreater(len(result), 0)
            self.assertLess(guard.current_batch_size, 10)
            self.assertGreater(len(guard.batch_sizes), 0)

    def test_memory_guard_process_batch_abort(self):
        """Test that processing aborts when batch size reaches minimum"""
        guard = MemoryGuard(MemoryConfig(
            threshold_percent=80.0,
            initial_batch_size=2,
            min_batch_size=2
        ))
        
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            with self.assertRaises(SystemExit):
                guard.process_batch(self.sample_batch)

    def test_memory_guard_get_current_batch_size(self):
        """Test getting current batch size"""
        guard = MemoryGuard(self.config)
        self.assertEqual(guard.get_current_batch_size(), 10)
        
        guard.current_batch_size = 5
        self.assertEqual(guard.get_current_batch_size(), 5)

    def test_memory_guard_reset_batch_size(self):
        """Test resetting batch size to initial"""
        guard = MemoryGuard(self.config)
        guard.current_batch_size = 5
        guard.reset_batch_size()
        self.assertEqual(guard.current_batch_size, 10)

    def test_memory_guard_get_downsample_history(self):
        """Test getting downsample history"""
        guard = MemoryGuard(self.config)
        
        with patch('utils.memory_guard.get_memory_usage_gb', return_value=85.0):
            guard.process_batch(self.sample_batch)
            guard.process_batch(self.sample_batch)
        
        history = guard.get_downsample_history()
        self.assertEqual(len(history), 2)
        self.assertIn(5, history)
        self.assertIn(2, history)

if __name__ == '__main__':
    unittest.main()