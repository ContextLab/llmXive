"""
Unit tests for code/utils/config.py
"""
import pytest
import os
import random
import numpy as np
import torch
from code.utils.config import (
    Config,
    get_default_config,
    create_config_with_overrides,
    DEFAULT_SEED,
    DEFAULT_ENTROPY_THRESHOLD,
    DEFAULT_GRADIENT_THRESHOLD,
    DEFAULT_RECENCY_THRESHOLD,
    SENSITIVITY_THRESHOLDS
)


class TestConfigInitialization:
    """Test Config class initialization and validation."""
    
    def test_default_config_creation(self):
        """Test that default config is created with expected values."""
        config = get_default_config()
        
        assert config.seed == DEFAULT_SEED
        assert config.device == "cpu"
        assert config.entropy_threshold == DEFAULT_ENTROPY_THRESHOLD
        assert config.gradient_threshold == DEFAULT_GRADIENT_THRESHOLD
        assert config.recency_threshold == DEFAULT_RECENCY_THRESHOLD
        assert config.context_window > 0
        assert config.batch_size > 0
    
    def test_custom_seed(self):
        """Test that custom seed is accepted."""
        config = Config(seed=123)
        assert config.seed == 123
    
    def test_cpu_device_enforcement(self):
        """Test that non-CPU devices are rejected."""
        with pytest.raises(ValueError, match="Device must be 'cpu'"):
            Config(device="cuda")
        
        with pytest.raises(ValueError, match="Device must be 'cpu'"):
            Config(device="mps")
    
    def test_invalid_entropy_threshold(self):
        """Test that invalid entropy thresholds are rejected."""
        with pytest.raises(ValueError, match="Entropy threshold must be between 0.0 and 1.0"):
            Config(entropy_threshold=1.5)
        
        with pytest.raises(ValueError, match="Entropy threshold must be between 0.0 and 1.0"):
            Config(entropy_threshold=-0.1)
    
    def test_invalid_gradient_threshold(self):
        """Test that invalid gradient thresholds are rejected."""
        with pytest.raises(ValueError, match="Gradient threshold must be between 0.0 and 1.0"):
            Config(gradient_threshold=2.0)
        
        with pytest.raises(ValueError, match="Gradient threshold must be between 0.0 and 1.0"):
            Config(gradient_threshold=-0.5)
    
    def test_invalid_recency_threshold(self):
        """Test that invalid recency thresholds are rejected."""
        with pytest.raises(ValueError, match="Recency threshold must be between 0.0 and 1.0"):
            Config(recency_threshold=1.2)
        
        with pytest.raises(ValueError, match="Recency threshold must be between 0.0 and 1.0"):
            Config(recency_threshold=-0.3)
    
    def test_invalid_context_window(self):
        """Test that invalid context windows are rejected."""
        with pytest.raises(ValueError, match="Context window must be positive"):
            Config(context_window=0)
        
        with pytest.raises(ValueError, match="Context window must be positive"):
            Config(context_window=-100)
    
    def test_invalid_batch_size(self):
        """Test that invalid batch sizes are rejected."""
        with pytest.raises(ValueError, match="Batch size must be positive"):
            Config(batch_size=0)
        
        with pytest.raises(ValueError, match="Batch size must be positive"):
            Config(batch_size=-1)
    
    def test_invalid_memory_limit(self):
        """Test that invalid memory limits are rejected."""
        with pytest.raises(ValueError, match="Memory limit must be positive"):
            Config(memory_limit_gb=0)
        
        with pytest.raises(ValueError, match="Memory limit must be positive"):
            Config(memory_limit_gb=-1.0)


class TestConfigMethods:
    """Test Config class methods."""
    
    def test_to_dict(self):
        """Test that to_dict returns all configuration values."""
        config = Config(seed=999, context_window=8192)
        config_dict = config.to_dict()
        
        assert config_dict["seed"] == 999
        assert config_dict["context_window"] == 8192
        assert config_dict["device"] == "cpu"
        assert "entropy_threshold" in config_dict
        assert "gradient_threshold" in config_dict
        assert "recency_threshold" in config_dict
    
    def test_from_dict(self):
        """Test that from_dict creates a valid Config instance."""
        config_dict = {
            "seed": 777,
            "context_window": 2048,
            "batch_size": 2,
            "entropy_threshold": 0.2,
            "device": "cpu"
        }
        
        config = Config.from_dict(config_dict)
        
        assert config.seed == 777
        assert config.context_window == 2048
        assert config.batch_size == 2
        assert config.entropy_threshold == 0.2
        assert config.device == "cpu"
    
    def test_get_thresholds(self):
        """Test that get_thresholds returns correct thresholds."""
        config = Config(
            entropy_threshold=0.15,
            gradient_threshold=0.08,
            recency_threshold=0.03
        )
        
        thresholds = config.get_thresholds()
        
        assert thresholds["entropy"] == 0.15
        assert thresholds["gradient"] == 0.08
        assert thresholds["recency"] == 0.03
    
    def test_get_sensitivity_thresholds(self):
        """Test that get_sensitivity_thresholds returns correct ranges."""
        config = get_default_config()
        sensitivity = config.get_sensitivity_thresholds()
        
        assert "entropy" in sensitivity
        assert "gradient" in sensitivity
        assert "recency" in sensitivity
        assert sensitivity["entropy"] == SENSITIVITY_THRESHOLDS
        assert sensitivity["gradient"] == SENSITIVITY_THRESHOLDS
        assert sensitivity["recency"] == SENSITIVITY_THRESHOLDS


class TestConfigOverrides:
    """Test config override functionality."""
    
    def test_create_config_with_overrides(self):
        """Test that create_config_with_overrides applies changes correctly."""
        overrides = {
            "seed": 555,
            "context_window": 4096,
            "batch_size": 4,
            "entropy_threshold": 0.25
        }
        
        config = create_config_with_overrides(overrides)
        
        assert config.seed == 555
        assert config.context_window == 4096
        assert config.batch_size == 4
        assert config.entropy_threshold == 0.25
        # Other values should be defaults
        assert config.gradient_threshold == DEFAULT_GRADIENT_THRESHOLD
        assert config.recency_threshold == DEFAULT_RECENCY_THRESHOLD
    
    def test_create_config_with_invalid_override(self):
        """Test that invalid overrides are rejected."""
        with pytest.raises(ValueError, match="Device must be 'cpu'"):
            create_config_with_overrides({"device": "cuda"})
        
        with pytest.raises(ValueError, match="Entropy threshold must be between 0.0 and 1.0"):
            create_config_with_overrides({"entropy_threshold": 1.5})


class TestSeedReproducibility:
    """Test seed initialization and reproducibility."""
    
    def test_seed_affects_random(self):
        """Test that setting seed affects random module."""
        config1 = Config(seed=42)
        val1 = random.random()
        
        config2 = Config(seed=42)
        val2 = random.random()
        
        assert val1 == val2
    
    def test_seed_affects_numpy(self):
        """Test that setting seed affects numpy."""
        config1 = Config(seed=42)
        arr1 = np.random.rand(5)
        
        config2 = Config(seed=42)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)
    
    def test_seed_affects_torch(self):
        """Test that setting seed affects torch."""
        config1 = Config(seed=42)
        t1 = torch.rand(5)
        
        config2 = Config(seed=42)
        t2 = torch.rand(5)
        
        assert torch.equal(t1, t2)


class TestModuleFunctions:
    """Test module-level convenience functions."""
    
    def test_get_default_config(self):
        """Test get_default_config returns valid config."""
        config = get_default_config()
        assert isinstance(config, Config)
        assert config.device == "cpu"
    
    def test_set_random_seed(self):
        """Test set_random_seed function."""
        from code.utils.config import set_random_seed
        
        set_random_seed(999)
        val1 = random.random()
        arr1 = np.random.rand(3)
        t1 = torch.rand(3)
        
        set_random_seed(999)
        val2 = random.random()
        arr2 = np.random.rand(3)
        t2 = torch.rand(3)
        
        assert val1 == val2
        assert np.array_equal(arr1, arr2)
        assert torch.equal(t1, t2)
    
    def test_get_heuristic_thresholds(self):
        """Test get_heuristic_thresholds function."""
        from code.utils.config import get_heuristic_thresholds
        
        thresholds = get_heuristic_thresholds()
        
        assert "entropy" in thresholds
        assert "gradient" in thresholds
        assert "recency" in thresholds
        assert thresholds["entropy"] == DEFAULT_ENTROPY_THRESHOLD
        assert thresholds["gradient"] == DEFAULT_GRADIENT_THRESHOLD
        assert thresholds["recency"] == DEFAULT_RECENCY_THRESHOLD
    
    def test_get_sensitivity_range(self):
        """Test get_sensitivity_range function."""
        from code.utils.config import get_sensitivity_range
        
        thresholds = get_sensitivity_range()
        assert thresholds == SENSITIVITY_THRESHOLDS
        assert len(thresholds) == 3
        assert 0.01 in thresholds
        assert 0.05 in thresholds
        assert 0.1 in thresholds