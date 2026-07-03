"""
Tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.config import Config, load_config, save_config, ensure_config_file, get_config


class TestConfigDataclass:
    """Test Config dataclass defaults."""

    def test_default_values(self):
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

    def test_custom_values(self):
        config = Config(seed=123, device="cuda")
        assert config.seed == 123
        assert config.device == "cuda"


class TestLoadConfig:
    """Test loading configuration from YAML."""

    def test_load_missing_file_returns_defaults(self, tmp_path):
        """When file is missing, defaults are returned."""
        config_path = tmp_path / "nonexistent.yaml"
        config = load_config(str(config_path))
        assert config.seed == 42
        assert config.device == "cpu"

    def test_load_partial_file_merges_with_defaults(self, tmp_path):
        """Missing keys are filled with defaults."""
        config_path = tmp_path / "partial.yaml"
        config_path.write_text("seed: 999\n")
        config = load_config(str(config_path))
        assert config.seed == 999
        assert config.device == "cpu"  # default
        assert config.model_name == "facebook/opt-125m"  # default

    def test_load_full_file(self, tmp_path):
        """Full configuration is loaded correctly."""
        config_path = tmp_path / "full.yaml"
        config_path.write_text(
            "seed: 456\n"
            "device: cuda\n"
            "model_name: test-model\n"
            "agent_counts: [2, 4, 6]\n"
        )
        config = load_config(str(config_path))
        assert config.seed == 456
        assert config.device == "cuda"
        assert config.model_name == "test-model"
        assert config.agent_counts == [2, 4, 6]

    def test_load_list_values(self, tmp_path):
        """List values are parsed correctly."""
        config_path = tmp_path / "lists.yaml"
        config_path.write_text("agent_counts: [1, 2, 3]\ncontext_windows: [64, 128]\n")
        config = load_config(str(config_path))
        assert config.agent_counts == [1, 2, 3]
        assert config.context_windows == [64, 128]


class TestSaveConfig:
    """Test saving configuration to YAML."""

    def test_save_and_reload(self, tmp_path):
        """Saved configuration can be reloaded."""
        config_path = tmp_path / "test.yaml"
        original = Config(seed=789, device="mps", num_games_full=500)
        save_config(original, str(config_path))
        
        assert config_path.exists()
        
        loaded = load_config(str(config_path))
        assert loaded.seed == 789
        assert loaded.device == "mps"
        assert loaded.num_games_full == 500

    def test_save_creates_directory(self, tmp_path):
        """Save creates parent directories if needed."""
        config_path = tmp_path / "subdir" / "test.yaml"
        config = Config()
        save_config(config, str(config_path))
        assert config_path.exists()


class TestEnsureConfigFile:
    """Test ensure_config_file function."""

    def test_creates_file_when_missing(self, tmp_path, monkeypatch):
        """Creates a default config file when none exists."""
        monkeypatch.chdir(tmp_path)
        config_path = ensure_config_file()
        
        assert config_path.exists()
        assert config_path.name == "config.yaml"
        
        # Verify it has defaults
        config = load_config(str(config_path))
        assert config.seed == 42
        assert config.device == "cpu"

    def test_returns_existing_file(self, tmp_path, monkeypatch):
        """Returns existing file without modification."""
        monkeypatch.chdir(tmp_path)
        existing = tmp_path / "config.yaml"
        existing.write_text("seed: 111\n")
        
        result = ensure_config_file()
        assert result == existing
        assert existing.read_text() == "seed: 111\n"


class TestGetConfig:
    """Test get_config function."""

    def test_creates_and_returns_config(self, tmp_path, monkeypatch):
        """Creates default config if none exists and returns it."""
        monkeypatch.chdir(tmp_path)
        config = get_config()
        
        assert config.seed == 42
        assert config.device == "cpu"
        
        assert (tmp_path / "config.yaml").exists()

    def test_returns_existing_config(self, tmp_path, monkeypatch):
        """Returns existing configuration."""
        monkeypatch.chdir(tmp_path)
        config_path = tmp_path / "config.yaml"
        config_path.write_text("seed: 222\n")
        
        config = get_config()
        assert config.seed == 222