"""
Tests for the configuration module.
"""
import os
import tempfile
import pytest
import yaml
from src.config import ProRLConfig, load_config, save_config


def test_default_config_values():
    """Test that default configuration has expected values."""
    config = ProRLConfig()
    assert config.path_length == 5
    assert config.alpha == 0.1
    assert config.beam_width == 50
    assert config.random_seed == 42
    assert config.similarity_threshold == 0.01
    assert config.max_items == 500000


def test_config_to_dict():
    """Test conversion of config to dictionary."""
    config = ProRLConfig(path_length=10, alpha=0.2)
    config_dict = config.to_dict()
    
    assert config_dict["path_length"] == 10
    assert config_dict["alpha"] == 0.2
    assert config_dict["beam_width"] == 50
    assert config_dict["random_seed"] == 42


def test_config_from_dict():
    """Test creation of config from dictionary."""
    data = {
        "path_length": 7,
        "alpha": 0.15,
        "beam_width": 100,
        "random_seed": 123,
        "similarity_threshold": 0.05,
        "max_items": 100000
    }
    config = ProRLConfig.from_dict(data)
    
    assert config.path_length == 7
    assert config.alpha == 0.15
    assert config.beam_width == 100
    assert config.random_seed == 123
    assert config.similarity_threshold == 0.05
    assert config.max_items == 100000


def test_load_config_from_file():
    """Test loading configuration from a YAML file."""
    config_data = {
        "path_length": 8,
        "alpha": 0.25,
        "beam_width": 75,
        "random_seed": 999
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        assert config.path_length == 8
        assert config.alpha == 0.25
        assert config.beam_width == 75
        assert config.random_seed == 999
    finally:
        os.unlink(temp_path)


def test_load_config_nonexistent_file():
    """Test that loading from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")


def test_load_config_none_returns_default():
    """Test that loading with None path returns default config."""
    config = load_config(None)
    assert config.path_length == 5
    assert config.alpha == 0.1


def test_save_and_load_config():
    """Test saving and loading configuration preserves values."""
    original_config = ProRLConfig(
        path_length=6,
        alpha=0.12,
        beam_width=60,
        random_seed=555,
        similarity_threshold=0.03,
        max_items=250000
    )
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name
    
    try:
        save_config(original_config, temp_path)
        
        # Verify file was created
        assert os.path.exists(temp_path)
        
        # Load and verify
        loaded_config = load_config(temp_path)
        assert loaded_config.path_length == 6
        assert loaded_config.alpha == 0.12
        assert loaded_config.beam_width == 60
        assert loaded_config.random_seed == 555
        assert loaded_config.similarity_threshold == 0.03
        assert loaded_config.max_items == 250000
    finally:
        os.unlink(temp_path)


def test_save_config_creates_directory():
    """Test that save_config creates parent directories if needed."""
    config = ProRLConfig()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = os.path.join(temp_dir, "subdir1", "subdir2", "config.yaml")
        save_config(config, nested_path)
        
        assert os.path.exists(nested_path)
