"""Tests for the configuration management module."""
import pytest
import tempfile
import os
from pathlib import Path
from code.utils.config import Config, load_config, save_config, ensure_config_file, get_config

def test_default_config_values():
    """Test that default configuration has correct seed and device."""
    config = Config()
    assert config.seed == 42
    assert config.device == "cpu"
    assert config.model_name == "facebook/opt-125m"
    assert config.dtype == "float32"

def test_save_and_load_config():
    """Test that config can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        
        # Create a config with custom values
        config = Config(seed=123, device="cpu", output_dir="custom_output")
        save_config(config, str(config_path))
        
        # Load it back
        loaded = load_config(str(config_path))
        
        assert loaded.seed == 123
        assert loaded.device == "cpu"
        assert loaded.output_dir == "custom_output"

def test_load_missing_config():
    """Test that loading a missing config returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.yaml"
        config = load_config(str(config_path))
        
        assert config.seed == 42
        assert config.device == "cpu"

def test_ensure_config_file_creates_default():
    """Test that ensure_config_file creates a default config if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        config_path = Path(tmpdir) / "config.yaml"
        
        # Remove if exists
        if config_path.exists():
            config_path.unlink()
        
        result_path = ensure_config_file()
        
        assert result_path.exists()
        loaded = load_config(str(result_path))
        assert loaded.seed == 42
        assert loaded.device == "cpu"

def test_config_merge_partial_file():
    """Test that partial config files merge with defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "partial_config.yaml"
        
        # Write only seed
        with open(config_path, "w") as f:
            f.write("seed: 999\n")
        
        config = load_config(str(config_path))
        
        assert config.seed == 999
        assert config.device == "cpu"  # Default
        assert config.model_name == "facebook/opt-125m"  # Default

def test_get_config_ensures_file():
    """Test that get_config ensures the config file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Ensure no config exists
        config_path = Path(tmpdir) / "config.yaml"
        if config_path.exists():
            config_path.unlink()
        
        config = get_config()
        
        assert config_path.exists()
        assert config.seed == 42
        assert config.device == "cpu"