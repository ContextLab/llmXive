import os
import pytest
from pathlib import Path
from config import Config, get_config, reload_config, get_nasa_power_key
from utils import get_project_root

def test_config_initialization():
    """Test that Config initializes without errors."""
    cfg = Config()
    assert cfg is not None
    assert cfg.project_root == get_project_root()

def test_get_config_singleton():
    """Test that get_config returns a singleton instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_reload_config():
    """Test that reload_config creates a new instance."""
    cfg1 = get_config()
    cfg2 = reload_config()
    assert cfg1 is not cfg2

def test_nasa_power_key_from_env(monkeypatch):
    """Test retrieving NASA POWER key from environment variable."""
    test_key = "test_api_key_123"
    monkeypatch.setenv("NASA_POWER_API_KEY", test_key)
    
    # Force reload to pick up env var
    cfg = reload_config()
    key = get_nasa_power_key()
    
    assert key == test_key

def test_nasa_power_key_from_config(monkeypatch):
    """Test retrieving NASA POWER key from config file if env is missing."""
    # Ensure env is not set
    monkeypatch.delenv("NASA_POWER_API_KEY", raising=False)
    
    # Create a temporary config with a key
    cfg = reload_config()
    cfg.set("api_keys.nasa_power", "config_key_456")
    
    key = get_nasa_power_key()
    assert key == "config_key_456"

def test_nasa_power_key_priority():
    """Test that env var takes precedence over config file."""
    cfg = reload_config()
    cfg.set("api_keys.nasa_power", "config_key")
    
    # Env var should override
    os.environ["NASA_POWER_API_KEY"] = "env_key"
    key = get_nasa_power_key()
    assert key == "env_key"
    
    # Cleanup
    del os.environ["NASA_POWER_API_KEY"]

def test_get_method():
    """Test the dot-notation get method."""
    cfg = Config()
    # Test existing key
    val = cfg.get("simulation.default_days")
    assert val == 365
    
    # Test missing key
    val = cfg.get("non.existent.key", "default")
    assert val == "default"
