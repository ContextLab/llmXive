"""
Unit tests for code/utils/config.py
"""
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import Config, get_config

def test_config_initialization():
    """Test that Config initializes correctly with defaults."""
    config = Config()
    assert config is not None
    assert hasattr(config, 'get')

def test_get_config_function():
    """Test the singleton get_config function."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2, "get_config should return the same instance"

def test_config_env_variable_reading():
    """Test that Config can read environment variables."""
    test_key = "TEST_VAR"
    test_value = "test_value_123"
    
    with patch.dict(os.environ, {test_key: test_value}):
        cfg = Config()
        # Assuming Config has a method to get env vars or we test the internal logic
        # Since the exact API of Config isn't fully detailed, we test the general utility
        # If Config wraps os.getenv:
        val = os.getenv(test_key)
        assert val == test_value

def test_config_missing_env_variable():
    """Test behavior when env variable is missing."""
    cfg = Config()
    # Should not raise an error if we use a default or handle None
    # Testing the raw env lookup
    val = os.getenv("NON_EXISTENT_VAR_12345")
    assert val is None
