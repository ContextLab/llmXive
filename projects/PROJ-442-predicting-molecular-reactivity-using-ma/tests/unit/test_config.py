"""
Unit tests for the configuration management system.
"""
import os
import tempfile
from pathlib import Path
import yaml
import pytest
from src.modeling.config import Config, load_config, get_config

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "test": {
                "key1": "value1",
                "key2": 42,
                "nested": {
                    "deep": "value"
                }
            }
        }
        yaml.dump(config_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_config_initialization_from_file(temp_config_file):
    """Test that Config loads correctly from a file."""
    # Create a temporary directory to act as project root
    with tempfile.TemporaryDirectory() as tmpdir:
        # Move the temp file to the temp dir
        dest = Path(tmpdir) / "test_config.yaml"
        import shutil
        shutil.move(temp_config_file, dest)
        
        # Create a mock Config that uses our temp file
        cfg = Config()
        # Force reload from our test file by manipulating the path
        # (In real usage, we'd pass the path to __init__)
        cfg._config_data = load_config(str(dest))
        
        assert cfg.get("test.key1") == "value1"
        assert cfg.get("test.key2") == 42
        assert cfg.get("test.nested.deep") == "value"

def test_config_dot_notation_access(temp_config_file):
    """Test dot notation access to config values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "test_config.yaml"
        import shutil
        shutil.move(temp_config_file, dest)
        
        cfg = Config()
        cfg._config_data = load_config(str(dest))
        
        assert cfg["test.key1"] == "value1"
        assert "test.key2" in cfg

def test_config_get_with_default():
    """Test get method with default value."""
    cfg = Config()
    # Reset to ensure we have a clean state for this test
    cfg._config_data = {}
    
    assert cfg.get("nonexistent.key", "default") == "default"
    assert cfg.get("another.missing", 0) == 0

def test_config_set_value():
    """Test setting configuration values."""
    cfg = Config()
    cfg._config_data = {}
    
    cfg.set("new.key", "value")
    assert cfg.get("new.key") == "value"
    
    cfg.set("nested.deep.key", 123)
    assert cfg.get("nested.deep.key") == 123

def test_config_to_dict():
    """Test conversion to dictionary."""
    cfg = Config()
    cfg._config_data = {"a": 1, "b": {"c": 2}}
    
    d = cfg.to_dict()
    assert d == {"a": 1, "b": {"c": 2}}
    assert d is not cfg._config_data  # Should be a copy

def test_load_config_function():
    """Test the standalone load_config function."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"test": "value"}, f)
        temp_path = f.name
    
    try:
        config_dict = load_config(temp_path)
        assert config_dict["test"] == "value"
    finally:
        os.unlink(temp_path)

def test_config_defaults_when_file_missing():
    """Test that defaults are created when config file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Point to a non-existent file
        fake_path = Path(tmpdir) / "nonexistent.yaml"
        
        cfg = Config()
        cfg._config_data = load_config(str(fake_path))
        
        # Should have default project name
        assert cfg.get("project.name") is not None
        assert "PROJ-442" in cfg.get("project.name")

def test_config_reload():
    """Test reloading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        
        # Create initial config
        initial_data = {"version": "1.0"}
        with open(config_file, 'w') as f:
            yaml.dump(initial_data, f)
        
        cfg = Config()
        cfg._config_data = load_config(str(config_file))
        assert cfg.get("version") == "1.0"
        
        # Update config file
        updated_data = {"version": "2.0"}
        with open(config_file, 'w') as f:
            yaml.dump(updated_data, f)
        
        # Reload
        cfg.reload(str(config_file))
        assert cfg.get("version") == "2.0"