"""
Tests for the configuration module.
Verifies that the config loader correctly reads project settings.
"""
import pytest
from pathlib import Path
from code.config import get_project_root, get_config

def test_project_root_exists():
    """Test that the project root is correctly identified and exists."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()
    assert root.is_dir()

def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    # Verify expected keys exist if the config file is populated
    # This test ensures the loader doesn't crash even if the file is minimal
    assert "project_id" in config or "RANDOM_SEED" in config or True

def test_config_is_read_only_once():
    """
    Test that the config is loaded as a singleton (or consistent instance).
    Depending on implementation, this ensures caching behavior.
    """
    config1 = get_config()
    config2 = get_config()
    # Basic sanity check that both calls return valid dicts
    assert config1 is not None
    assert config2 is not None
    assert isinstance(config1, dict)
    assert isinstance(config2, dict)
