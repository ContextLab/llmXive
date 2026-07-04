"""
Unit tests for the configuration module.
"""
import os
import pytest
from pathlib import Path

# Import the module to test
from code.utils.config import Config, get_config, reset_config


def test_config_defaults():
    """Test that Config initializes with correct defaults."""
    config = Config()
    assert config.model_seed == 42
    assert config.n_estimators == 100
    assert config.max_depth == 10
    assert config.min_r2_score == 0.8
    assert config.window_days == 30
    assert config.significance_level == 0.05
    assert config.n_permutations == 1000


def test_config_from_env(monkeypatch):
    """Test that Config reads from environment variables."""
    monkeypatch.setenv("MODEL_SEED", "123")
    monkeypatch.setenv("N_ESTIMATORS", "200")
    monkeypatch.setenv("MIN_R2_SCORE", "0.9")
    monkeypatch.setenv("WINDOW_DAYS", "60")
    
    reset_config()  # Ensure we get fresh config
    config = get_config()
    
    assert config.model_seed == 123
    assert config.n_estimators == 200
    assert config.min_r2_score == 0.9
    assert config.window_days == 60
    
    reset_config()


def test_singleton_pattern():
    """Test that get_config returns the same instance."""
    reset_config()
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
    
    reset_config()
