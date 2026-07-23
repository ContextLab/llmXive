import pytest
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_config, get_default_paths, get_default_hyperparameters, DEFAULT_PATHS, DEFAULT_HYPERPARAMETERS

def test_get_config_no_args():
    """Test get_config() with no arguments returns defaults."""
    config = get_config()
    assert "paths" in config
    assert "hyperparameters" in config
    assert config["paths"] == DEFAULT_PATHS
    assert config["hyperparameters"] == DEFAULT_HYPERPARAMETERS

def test_get_config_none():
    """Test get_config(None) returns defaults."""
    config = get_config(None)
    assert config["paths"] == DEFAULT_PATHS

def test_get_config_empty_string():
    """Test get_config("") returns defaults."""
    config = get_config("")
    assert config["paths"] == DEFAULT_PATHS

def test_get_config_valid_file():
    """Test get_config with a valid YAML file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
        paths:
          data_raw: /custom/raw
        hyperparameters:
          sample_size: 50
        """)
        temp_path = f.name

    try:
        config = get_config(temp_path)
        assert config["paths"]["data_raw"] == "/custom/raw"
        assert config["hyperparameters"]["sample_size"] == 50
        # Default values should still be present for non-overridden keys
        assert "data_derived" in config["paths"]
        assert "batch_size" in config["hyperparameters"]
    finally:
        os.unlink(temp_path)

def test_get_config_missing_file():
    """Test get_config with a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        get_config("/non/existent/path/config.yaml")

def test_get_default_paths():
    """Test get_default_paths returns a copy of defaults."""
    paths = get_default_paths()
    assert paths == DEFAULT_PATHS
    assert paths is not DEFAULT_PATHS  # Should be a copy

def test_get_default_hyperparameters():
    """Test get_default_hyperparameters returns a copy of defaults."""
    hparams = get_default_hyperparameters()
    assert hparams == DEFAULT_HYPERPARAMETERS
    assert hparams is not DEFAULT_HYPERPARAMETERS  # Should be a copy
