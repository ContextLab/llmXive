"""
Unit tests for code/config.py (T002: Seed Pinning and Configuration).
"""
import os
import random
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.config import (
    Config, 
    ConfigException, 
    get_config, 
    set_global_seed, 
    GLOBAL_SEED,
    _config_instance
)

@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset the config singleton before each test to ensure isolation."""
    # Clear the singleton
    import code.config
    code.config._config_instance = None
    yield
    # Cleanup after test
    code.config._config_instance = None

def test_config_defaults():
    """Test that Config loads with correct default values."""
    cfg = Config()
    assert cfg.model_path == "Salesforce/codegen-350M-mono"
    assert cfg.quantization_bits == 4
    assert cfg.rate_limit_retries == 3
    assert cfg.rate_limit_backoff == 5.0
    assert cfg.max_memory_mb == 7000
    assert cfg.device == "cpu"
    assert cfg.seed == 42

def test_config_env_override():
    """Test that Config respects environment variable overrides."""
    with patch.dict(os.environ, {
        "CODEGEN_MODEL_PATH": "custom/model",
        "QUANTIZATION_BITS": "8",
        "RATE_LIMIT_RETRIES": "5",
        "MAX_MEMORY_MB": "10000",
        "DEVICE": "cuda",
        "RANDOM_SEED": "123"
    }):
        cfg = Config()
        assert cfg.model_path == "custom/model"
        assert cfg.quantization_bits == 8
        assert cfg.rate_limit_retries == 5
        assert cfg.max_memory_mb == 10000
        assert cfg.device == "cuda"
        assert cfg.seed == 123

def test_config_invalid_quantization_bits():
    """Test that Config raises an exception for invalid quantization bits."""
    with patch.dict(os.environ, {"QUANTIZATION_BITS": "7"}):
        with pytest.raises(ConfigException, match="Quantization bits must be 4, 8, 16, or 32"):
            Config()

def test_config_invalid_device():
    """Test that Config raises an exception for invalid device."""
    with patch.dict(os.environ, {"DEVICE": "invalid_device"}):
        with pytest.raises(ConfigException, match="Invalid device"):
            Config()

def test_seed_reproducibility():
    """Test that set_global_seed produces deterministic results."""
    # Set seed and generate data
    set_global_seed(42)
    result_1 = {
        'random': random.random(),
        'numpy': np.random.rand(5).tolist(),
    }
    
    # Reset seed and generate data again
    set_global_seed(42)
    result_2 = {
        'random': random.random(),
        'numpy': np.random.rand(5).tolist(),
    }
    
    # Results should be identical
    assert result_1 == result_2

def test_seed_different_values():
    """Test that different seeds produce different results."""
    set_global_seed(42)
    result_1 = random.random()
    
    set_global_seed(123)
    result_2 = random.random()
    
    # Results should be different (with very high probability)
    assert result_1 != result_2

def test_config_singleton():
    """Test that get_config returns the same instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_config_to_dict():
    """Test that to_dict returns a correct dictionary representation."""
    cfg = Config()
    d = cfg.to_dict()
    assert "model_path" in d
    assert "quantization_bits" in d
    assert "seed" in d
    assert d["model_path"] == cfg.model_path
    assert d["seed"] == cfg.seed