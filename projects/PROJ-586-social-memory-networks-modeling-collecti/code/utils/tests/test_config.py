"""
Tests for the configuration management module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from utils.config import Config, load_config, save_config, ensure_config_file, get_config

def test_config_default_values():
    """Test that default config has required values."""
    config = Config()
    assert config.seed == 42
    assert config.device == "cpu"
    assert config.model_name == "facebook/opt-125m"
    assert config.dtype == "float32"

def test_load_config_from_missing_file():
    """Test loading config from a non-existent file returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.yaml"
        config = load_config(str(config_path))
        assert config.seed == 42
        assert config.device == "cpu"

def test_load_config_from_file():
    """Test loading config from an existing YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        # Write a custom config
        with open(config_path, "w") as f:
            f.write("seed: 123\n")
            f.write("device: cpu\n")
            f.write("model_name: test-model\n")
        
        config = load_config(str(config_path))
        assert config.seed == 123
        assert config.device == "cpu"
        assert config.model_name == "test-model"

def test_save_and_load_config():
    """Test that saving and loading config preserves values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        
        # Create and save config
        config = Config(seed=999, device="cpu", model_name="custom-model")
        save_config(config, str(config_path))
        
        # Load and verify
        loaded_config = load_config(str(config_path))
        assert loaded_config.seed == 999
        assert loaded_config.device == "cpu"
        assert loaded_config.model_name == "custom-model"

def test_ensure_config_file_creates_default():
    """Test that ensure_config_file creates a default config if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        # Ensure file doesn't exist
        assert not config_path.exists()
        
        # Call ensure_config_file
        result_path = ensure_config_file.__globals__['Path'] = Path
        # We need to mock the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = ensure_config_file()
            assert result.exists()
            # Verify it has defaults
            config = load_config(str(result))
            assert config.seed == 42
            assert config.device == "cpu"
        finally:
            os.chdir(original_cwd)

def test_config_with_list_fields():
    """Test that list fields are properly handled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        
        # Create config with list fields
        config = Config(
            seed=42,
            device="cpu",
            agent_counts=[2, 4, 6],
            context_windows=[64, 128, 256]
        )
        save_config(config, str(config_path))
        
        # Load and verify
        loaded_config = load_config(str(config_path))
        assert loaded_config.agent_counts == [2, 4, 6]
        assert loaded_config.context_windows == [64, 128, 256]
