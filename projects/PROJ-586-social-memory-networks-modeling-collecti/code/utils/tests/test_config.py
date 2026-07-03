"""Tests for the environment configuration module."""
import pytest
import json
import tempfile
from pathlib import Path

from utils.config import (
    load_config,
    save_config,
    get_config_value,
    set_seed,
    set_device,
    DEFAULT_CONFIG,
    DEFAULT_CONFIG_PATH,
)


class TestLoadConfig:
    def test_load_missing_file_returns_defaults(self):
        """Loading a non-existent config should return defaults."""
        config = load_config(Path("/nonexistent/path/config.yaml"))
        assert config["seed"] == 42
        assert config["device"] == "cpu"
        assert config["experiment_name"] == "social-memory-networks"

    def test_load_yaml_file(self, tmp_path):
        """Loading a YAML file should parse it correctly."""
        config_data = {
            "seed": 123,
            "device": "cuda",
            "custom_key": "custom_value"
        }
        config_file = tmp_path / "config.yaml"
        import yaml
        with config_file.open("w") as f:
            yaml.safe_dump(config_data, f)

        config = load_config(config_file)
        assert config["seed"] == 123
        assert config["device"] == "cuda"
        assert config["custom_key"] == "custom_value"
        # Defaults should still be present for missing keys
        assert config["experiment_name"] == "social-memory-networks"

    def test_load_json_file(self, tmp_path):
        """Loading a JSON file should parse it correctly."""
        config_data = {
            "seed": 456,
            "device": "cpu"
        }
        config_file = tmp_path / "config.json"
        with config_file.open("w") as f:
            json.dump(config_data, f)

        config = load_config(config_file)
        assert config["seed"] == 456
        assert config["device"] == "cpu"

    def test_yaml_overrides_defaults(self, tmp_path):
        """YAML values should override defaults."""
        config_data = {"seed": 999}
        config_file = tmp_path / "config.yaml"
        import yaml
        with config_file.open("w") as f:
            yaml.safe_dump(config_data, f)

        config = load_config(config_file)
        assert config["seed"] == 999
        assert config["device"] == "cpu"  # Default preserved


class TestSaveConfig:
    def test_save_yaml(self, tmp_path):
        """Saving should create a YAML file by default."""
        config_data = {"seed": 789, "device": "cuda"}
        config_file = tmp_path / "config.yaml"

        save_config(config_data, config_file)

        assert config_file.exists()
        import yaml
        with config_file.open("r") as f:
            loaded = yaml.safe_load(f)
        assert loaded["seed"] == 789
        assert loaded["device"] == "cuda"

    def test_save_json_fallback(self, tmp_path, monkeypatch):
        """Saving should fallback to JSON if YAML fails."""
        # Force YAML to fail by making import fail
        import utils.config as config_module

        def mock_import_yaml(*args, **kwargs):
            raise ImportError("No module named 'yaml'")

        monkeypatch.setattr(config_module, "yaml", None)

        config_data = {"seed": 111, "device": "cpu"}
        config_file = tmp_path / "config.json"

        save_config(config_data, config_file)

        assert config_file.exists()
        with config_file.open("r") as f:
            loaded = json.load(f)
        assert loaded["seed"] == 111


class TestGetConfigValue:
    def test_get_top_level(self):
        """Getting a top-level key should return the value."""
        value = get_config_value("seed")
        assert value == 42

    def test_get_nested(self):
        """Getting a nested key should return the value."""
        value = get_config_value("agents.default_model")
        assert value == "opt-125m"

    def test_get_missing_with_default(self):
        """Getting a missing key should return the provided default."""
        value = get_config_value("nonexistent.key", default="fallback")
        assert value == "fallback"

    def test_get_missing_without_default(self):
        """Getting a missing key without default should return None."""
        value = get_config_value("nonexistent.key")
        assert value is None

    def test_get_with_custom_path(self, tmp_path):
        """Getting a value should use the custom path."""
        config_data = {"seed": 222}
        config_file = tmp_path / "config.yaml"
        import yaml
        with config_file.open("w") as f:
            yaml.safe_dump(config_data, f)

        value = get_config_value("seed", path=config_file)
        assert value == 222


class TestSetSeed:
    def test_set_seed_updates_config(self, tmp_path):
        """Setting a seed should update and save the config."""
        config_file = tmp_path / "config.yaml"
        set_seed(555, path=config_file)

        config = load_config(config_file)
        assert config["seed"] == 555

    def test_set_seed_none_uses_default(self, tmp_path):
        """Setting seed to None should use the default or existing value."""
        config_file = tmp_path / "config.yaml"
        # First set a value
        set_seed(333, path=config_file)
        # Then set to None
        set_seed(None, path=config_file)

        config = load_config(config_file)
        assert config["seed"] == 333  # Should keep existing value


class TestSetDevice:
    def test_set_device_updates_config(self, tmp_path):
        """Setting a device should update and save the config."""
        config_file = tmp_path / "config.yaml"
        set_device("cuda", path=config_file)

        config = load_config(config_file)
        assert config["device"] == "cuda"

    def test_set_device_cpu(self, tmp_path):
        """Setting device to cpu should work."""
        config_file = tmp_path / "config.yaml"
        set_device("cpu", path=config_file)

        config = load_config(config_file)
        assert config["device"] == "cpu"
