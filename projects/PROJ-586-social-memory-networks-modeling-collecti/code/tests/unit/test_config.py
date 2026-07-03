"""
Unit tests for the environment management configuration module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from dataclasses import asdict

# Import the module under test
from utils.config import Config, load_config, save_config, ensure_config_file, get_config

class TestConfigDataclass:
    """Tests for the Config dataclass defaults."""

    def test_default_seed_is_42(self):
        config = Config()
        assert config.seed == 42

    def test_default_device_is_cpu(self):
        config = Config()
        assert config.device == "cpu"

    def test_default_model_name(self):
        config = Config()
        assert config.model_name == "facebook/opt-125m"

    def test_default_dtype_is_float32(self):
        config = Config()
        assert config.dtype == "float32"

    def test_default_agent_counts(self):
        config = Config()
        assert config.agent_counts == [3, 5, 7]

    def test_default_context_windows(self):
        config = Config()
        assert config.context_windows == [128, 256, 512]

class TestLoadSaveConfig:
    """Tests for load_config and save_config functions."""

    def test_save_and_load_config(self, tmp_path):
        """Test that a config can be saved and loaded correctly."""
        config_path = tmp_path / "test_config.yaml"
        
        original_config = Config(seed=123, device="cpu", num_games_full=500)
        save_config(original_config, str(config_path))
        
        assert config_path.exists()
        
        loaded_config = load_config(str(config_path))
        assert loaded_config.seed == 123
        assert loaded_config.device == "cpu"
        assert loaded_config.num_games_full == 500

    def test_load_missing_file_returns_defaults(self, tmp_path):
        """Test that loading a non-existent file returns defaults."""
        config_path = tmp_path / "nonexistent.yaml"
        config = load_config(str(config_path))
        
        assert config.seed == 42
        assert config.device == "cpu"

    def test_partial_config_file_uses_defaults_for_missing(self, tmp_path):
        """Test that missing keys in config file are filled with defaults."""
        config_path = tmp_path / "partial_config.yaml"
        config_path.write_text("seed: 99\n")
        
        config = load_config(str(config_path))
        
        assert config.seed == 99
        assert config.device == "cpu"  # Default
        assert config.model_name == "facebook/opt-125m"  # Default

class TestEnsureConfigFile:
    """Tests for ensure_config_file function."""

    def test_creates_file_if_missing(self, tmp_path, monkeypatch):
        """Test that ensure_config_file creates a config.yaml if it doesn't exist."""
        # Change to tmp_path to avoid writing to actual project root
        monkeypatch.chdir(tmp_path)
        
        config_path = ensure_config_file()
        
        assert config_path.exists()
        assert config_path.name == "config.yaml"
        
        # Verify contents have correct defaults
        content = config_path.read_text()
        assert "seed: 42" in content
        assert "device: cpu" in content

    def test_does_not_overwrite_existing(self, tmp_path, monkeypatch):
        """Test that ensure_config_file does not overwrite an existing file."""
        monkeypatch.chdir(tmp_path)
        
        config_path = tmp_path / "config.yaml"
        config_path.write_text("seed: 12345\n")
        
        result_path = ensure_config_file()
        
        assert result_path == config_path
        content = config_path.read_text()
        assert "seed: 12345" in content

class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_creates_and_loads(self, tmp_path, monkeypatch):
        """Test that get_config ensures file exists and loads it."""
        monkeypatch.chdir(tmp_path)
        
        config = get_config()
        
        assert config.seed == 42
        assert config.device == "cpu"
        assert (tmp_path / "config.yaml").exists()
