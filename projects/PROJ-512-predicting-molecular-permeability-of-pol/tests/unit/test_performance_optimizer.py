"""
Unit tests for the performance optimization module.

Tests cover:
- FeatureCache functionality
- PerformanceConfig validation
- OptimizedDataLoader initialization
- Environment optimization
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.performance_optimizer import (
    PerformanceConfig,
    FeatureCache,
    OptimizedDataLoader,
    optimize_environment,
    run_optimized_training
)


class TestPerformanceConfig:
    """Tests for PerformanceConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = PerformanceConfig()
        assert config.max_runtime_seconds == 21600  # 6 hours
        assert config.enable_feature_cache is True
        assert config.cache_dir == "data/cache"
        assert config.num_workers == 4
        assert config.batch_size == 32
        assert config.early_termination_threshold == 0.95
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = PerformanceConfig(
            max_runtime_seconds=3600,
            enable_feature_cache=False,
            cache_dir="custom/cache",
            num_workers=8,
            batch_size=64
        )
        assert config.max_runtime_seconds == 3600
        assert config.enable_feature_cache is False
        assert config.cache_dir == "custom/cache"
        assert config.num_workers == 8
        assert config.batch_size == 64


class TestFeatureCache:
    """Tests for FeatureCache class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.test_dir, "cache")
        self.cache = FeatureCache(self.cache_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache.get("nonexistent_key")
        assert result is None
        stats = self.cache.get_stats()
        assert stats['misses'] == 1
    
    def test_cache_set_and_get(self):
        """Test setting and getting values."""
        test_data = {"key": "value", "number": 42}
        self.cache.set("test_key", test_data)
        
        result = self.cache.get("test_key")
        assert result == test_data
        
        stats = self.cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 0
    
    def test_cache_persistence(self):
        """Test that cache persists to disk."""
        test_data = {"persistent": True}
        self.cache.set("persist_key", test_data)
        
        # Create a new cache instance
        new_cache = FeatureCache(self.cache_dir)
        result = new_cache.get("persist_key")
        assert result == test_data
    
    def test_cache_key_uniqueness(self):
        """Test that different data produces different keys."""
        self.cache.set("data1", {"value": 1})
        self.cache.set("data2", {"value": 2})
        
        result1 = self.cache.get("data1")
        result2 = self.cache.get("data2")
        
        assert result1 == {"value": 1}
        assert result2 == {"value": 2}
        assert result1 != result2


class TestOptimizedDataLoader:
    """Tests for OptimizedDataLoader class."""
    
    def test_initialization(self):
        """Test DataLoader initialization with default config."""
        config = PerformanceConfig()
        dummy_dataset = list(range(10))
        
        dataloader = OptimizedDataLoader(dummy_dataset, config)
        assert len(dataloader) > 0
        assert dataloader.config == config
    
    def test_iteration(self):
        """Test that iteration works correctly."""
        config = PerformanceConfig(batch_size=2)
        dummy_dataset = list(range(10))
        
        dataloader = OptimizedDataLoader(dummy_dataset, config)
        batches = list(dataloader)
        
        assert len(batches) > 0
        assert all(len(batch) <= config.batch_size for batch in batches)
    
    def test_elapsed_time_tracking(self):
        """Test that elapsed time is tracked correctly."""
        config = PerformanceConfig()
        dummy_dataset = list(range(10))
        
        dataloader = OptimizedDataLoader(dummy_dataset, config)
        
        # Start iteration
        iter(dataloader)
        time.sleep(0.1)
        
        elapsed = dataloader.get_elapsed_time()
        assert elapsed >= 0.1


class TestEnvironmentOptimization:
    """Tests for environment optimization functions."""
    
    @patch('os.environ')
    @patch('torch.set_num_threads')
    def test_optimize_environment_sets_vars(self, mock_set_threads, mock_environ):
        """Test that environment variables are set correctly."""
        config = PerformanceConfig(num_workers=4)
        
        optimize_environment(config)
        
        # Check that environment variables were set
        calls = [call[0][0] for call in mock_environ.__setitem__.call_args_list]
        assert 'OMP_NUM_THREADS' in calls
        assert 'MKL_NUM_THREADS' in calls
        assert 'OPENBLAS_NUM_THREADS' in calls
        assert 'CUDA_VISIBLE_DEVICES' in calls


class TestRunOptimizedTraining:
    """Tests for the main optimization function."""
    
    @patch('performance_optimizer._run_default_training_pipeline')
    def test_run_optimized_training_generates_report(self, mock_training):
        """Test that a report is generated correctly."""
        # Mock the training result
        mock_training.return_value = {
            "final_loss": 0.5,
            "metrics": {"r2": 0.8},
            "epochs_completed": 5
        }
        
        config = PerformanceConfig(
            max_runtime_seconds=100,
            enable_feature_cache=False
        )
        
        with patch('os.makedirs'), patch('builtins.open', mock_open()):
            report = run_optimized_training(config)
        
        assert 'total_runtime_seconds' in report
        assert 'budget_met' in report
        assert 'training_result' in report


# Mock for file operations in tests
from unittest.mock import mock_open