"""
Unit tests for configuration management.
"""
import pytest
from utils.config import Config, get_config

def test_config_creation():
    """Test basic configuration creation."""
    config = Config(api_key="test_key", timeout=30)
    assert config.api_key == "test_key"
    assert config.timeout == 30

def test_get_config_singleton():
    """Test that get_config returns a consistent instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2
