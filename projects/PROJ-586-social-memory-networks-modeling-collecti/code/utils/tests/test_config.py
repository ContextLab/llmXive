"""
Tests for the configuration module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from utils.config import Config, load_config, save_config, ensure_config_file


def test_config_defaults():
    """Test that Config has correct default values."""
    config = Config()
    assert config.seed == 42
    assert config.device == "cpu"
    assert config.model_name == "facebook/opt-125m"
    assert config.dtype == "float32"
    assert config.log_file == "experiment.log"
    assert config.output_dir == "results"
    assert config.data_dir == "data"
    assert config.num_games_full == 1000
    assert config.num_games_limited == 1000
    assert config.agent_counts == [3, 5, 7]
    assert config.context_windows == [128, 256, 512]


def test_load_config_missing_file():
    """Test loading config when file doesn't exist returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.yaml"
        config = load_config(str(config_path))
        assert config.seed == 42
        assert config.device == "cpu"


def test_save_and_load_config():
    """Test that saving and loading config works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yaml"
        
        # Create and save a config
        original_config = Config(seed=123, device="cuda", agent_counts=[2, 4, 6])
        save_config(original_config, str(config_path))
        
        # Verify file exists
        assert config_path.exists()
        
        # Load the config back
        loaded_config = load_config(str(config_path))
        
        # Verify values match
        assert loaded_config.seed == 123
        assert loaded_config.device == "cuda"
        assert loaded_config.agent_counts == [2, 4, 6]


def test_load_config_partial_file():
    """Test that loading config with partial values uses defaults for missing keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "partial_config.yaml"
        
        # Create a partial config file
        with open(config_path, "w") as f:
            f.write("seed: 999\n")
            # device is missing, should default to "cpu"
        
        config = load_config(str(config_path))
        assert config.seed == 999
        assert config.device == "cpu"  # Default value


def test_ensure_config_file_creates():
    """Test that ensure_config_file creates a file if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory to avoid affecting project root
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config_path = ensure_config_file()
            
            # Verify file was created
            assert config_path.exists()
            assert config_path.name == "config.yaml"
            
            # Verify it has default values
            config = load_config(str(config_path))
            assert config.seed == 42
            assert config.device == "cpu"
        finally:
            os.chdir(old_cwd)


def test_ensure_config_file_uses_existing():
    """Test that ensure_config_file doesn't overwrite existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create a config with custom values
            custom_config = Config(seed=777, device="cuda")
            save_config(custom_config, "config.yaml")
            
            # Call ensure_config_file
            config_path = ensure_config_file()
            
            # Load and verify values are preserved
            config = load_config(str(config_path))
            assert config.seed == 777
            assert config.device == "cuda"
        finally:
            os.chdir(old_cwd)
