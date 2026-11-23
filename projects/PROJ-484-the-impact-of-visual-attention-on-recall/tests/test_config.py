"""
Unit tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# We need to reload the module to pick up new env vars if needed
import importlib

def test_get_config_defaults(monkeypatch):
    """Test that get_config returns defaults when .env is missing."""
    # Ensure no .env file is present by mocking the path
    with patch('config.ENV_FILE_PATH', Path('/nonexistent/.env')):
        # Reload module to pick up the new path
        import config
        importlib.reload(config)
        
        cfg = config.get_config()
        assert cfg["data_path"] == "./data"
        assert cfg["random_seed"] == 42

def test_get_data_path(monkeypatch):
    """Test get_data_path returns correct value."""
    monkeypatch.setenv("DATA_PATH", "/custom/data/path")
    import config
    importlib.reload(config)
    
    assert config.get_data_path() == "/custom/data/path"

def test_get_random_seed(monkeypatch):
    """Test get_random_seed returns correct value."""
    monkeypatch.setenv("RANDOM_SEED", "12345")
    import config
    importlib.reload(config)
    
    assert config.get_random_seed() == 12345

def test_validate_config_missing_data_path(monkeypatch):
    """Test that validate_config raises when DATA_PATH is missing."""
    monkeypatch.delenv("DATA_PATH", raising=False)
    import config
    importlib.reload(config)
    
    with pytest.raises(ValueError, match="DATA_PATH environment variable is not set"):
        config.validate_config()

def test_validate_config_invalid_seed(monkeypatch):
    """Test that validate_config raises when RANDOM_SEED is invalid."""
    monkeypatch.setenv("DATA_PATH", "./data")
    monkeypatch.setenv("RANDOM_SEED", "not_a_number")
    import config
    importlib.reload(config)
    
    with pytest.raises(ValueError, match="Invalid RANDOM_SEED"):
        config.validate_config()

def test_validate_config_negative_seed(monkeypatch):
    """Test that validate_config raises when RANDOM_SEED is negative."""
    monkeypatch.setenv("DATA_PATH", "./data")
    monkeypatch.setenv("RANDOM_SEED", "-10")
    import config
    importlib.reload(config)
    
    with pytest.raises(ValueError, match="RANDOM_SEED must be a non-negative integer"):
        config.validate_config()