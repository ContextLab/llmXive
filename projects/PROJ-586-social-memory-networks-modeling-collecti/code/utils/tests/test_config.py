"""
Tests for the configuration module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from utils.config import Config, load_config, save_config, ensure_config_file


def test_default_config_values():
    """Test that default configuration has correct seed and device."""
    config = Config()
    assert config.seed == 42
    assert config.device == "cpu"
    assert config.model_name == "facebook/opt-125m"


def test_save_and_load_config():
    """Test that config can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        
        # Create and save a config
        original_config = Config(seed=123, device="cpu", num_games_full=500)
        save_config(original_config, str(config_path))
        
        # Load it back
        loaded_config = load_config(str(config_path))
        
        assert loaded_config.seed == 123
        assert loaded_config.device == "cpu"
        assert loaded_config.num_games_full == 500


def test_load_missing_config_uses_defaults():
    """Test that loading a missing config returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.yaml"
        
        config = load_config(str(config_path))
        
        assert config.seed == 42
        assert config.device == "cpu"


def test_ensure_config_file_creates_file():
    """Test that ensure_config_file creates a file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp dir to avoid polluting project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config_path = Path("test_ensure_config.yaml")
            
            # Remove if exists
            if config_path.exists():
                config_path.unlink()
            
            # Ensure it exists
            result_path = ensure_config_file()
            
            assert result_path.exists()
            assert result_path.name == "test_ensure_config.yaml"
            
            # Verify content
            config = load_config(str(result_path))
            assert config.seed == 42
            assert config.device == "cpu"
        finally:
            os.chdir(original_cwd)


def test_config_with_custom_values():
    """Test loading config with custom values from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_config.yaml"
        
        # Create a custom config file
        with open(config_path, "w") as f:
            f.write("seed: 999\n")
            f.write("device: cpu\n")
            f.write("model_name: test-model\n")
            f.write("num_games_full: 2000\n")
        
        config = load_config(str(config_path))
        
        assert config.seed == 999
        assert config.device == "cpu"
        assert config.model_name == "test-model"
        assert config.num_games_full == 2000
