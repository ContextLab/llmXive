"""
Unit tests for code/config.py
"""
import pytest
from config import ExecutionConfig, get_config, set_config_override

def test_execution_config_defaults():
    """Test default values of ExecutionConfig."""
    config = ExecutionConfig()
    assert config.cpu_only is True
    assert config.time_limit_seconds is not None
    assert config.ram_limit_gb is not None
    assert config.random_seed is not None

def test_get_config_returns_instance():
    """Test that get_config returns an ExecutionConfig instance."""
    config = get_config()
    assert isinstance(config, ExecutionConfig)

def test_set_config_override():
    """Test that set_config_override modifies the config."""
    original_seed = get_config().random_seed
    set_config_override({"random_seed": 42})
    assert get_config().random_seed == 42
    # Reset to original
    set_config_override({"random_seed": original_seed})
