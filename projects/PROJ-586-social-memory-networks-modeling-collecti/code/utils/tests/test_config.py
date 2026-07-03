"""
Tests for the configuration management module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from utils.config import Config, load_config, save_config, ensure_config_file, get_config

def test_default_config_values():
    """Test that default configuration has the required seed and device."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        # Ensure file does not exist
        if config_path.exists():
            config_path.unlink()
        
        # Load config (should use defaults)
        config = load_config(str(config_path))
        
        assert config.seed == 42
        assert config.device == "cpu"
        assert config.model_name == "facebook/opt-125m"
        assert config.dtype == "float32"

def test_load_custom_config():
    """Test loading a custom configuration file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        # Create a custom config
        custom_config = Config(
            seed=123,
            device="cpu",
            model_name="test-model",
            num_games_full=500
        )
        save_config(custom_config, str(config_path))
        
        # Load and verify
        loaded = load_config(str(config_path))
        
        assert loaded.seed == 123
        assert loaded.model_name == "test-model"
        assert loaded.num_games_full == 500
        # Defaults should still apply for missing fields
        assert loaded.device == "cpu"

def test_save_and_load_roundtrip():
    """Test that saving and loading preserves all values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        
        original = Config(
            seed=999,
            device="cpu",
            agent_counts=[2, 4, 6],
            context_windows=[64, 128]
        )
        save_config(original, str(config_path))
        
        loaded = load_config(str(config_path))
        
        assert loaded.seed == 999
        assert loaded.agent_counts == [2, 4, 6]
        assert loaded.context_windows == [64, 128]

def test_ensure_config_file_creates_default():
    """Test that ensure_config_file creates a default config if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        config_path = Path(tmpdir) / "config.yaml"
        
        # Remove if exists
        if config_path.exists():
            config_path.unlink()
        
        result_path = ensure_config_file()
        
        assert result_path == config_path
        assert config_path.exists()
        
        # Verify it has default values
        config = load_config(str(config_path))
        assert config.seed == 42
        assert config.device == "cpu"

def test_get_config_returns_singleton_like_behavior():
    """Test that get_config ensures config file exists and returns it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        config_path = Path(tmpdir) / "config.yaml"
        
        # Ensure file does not exist
        if config_path.exists():
            config_path.unlink()
        
        config = get_config()
        
        assert config.seed == 42
        assert config.device == "cpu"
        assert config_path.exists()