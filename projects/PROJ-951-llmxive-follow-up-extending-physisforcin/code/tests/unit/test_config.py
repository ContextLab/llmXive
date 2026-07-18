"""
Unit tests for the training configuration management module.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path
from src.training.config import (
    TrainingConfig,
    create_default_config,
    get_default_config,
    load_config,
    validate_config_schema,
    save_config,
    get_filter_discard_threshold,
    get_config,
    DEFAULT_CONFIG,
    REQUIRED_KEYS,
)


class TestTrainingConfig:
    """Tests for the TrainingConfig dataclass."""

    def test_create_default_config(self):
        """Test that default config is created with expected values."""
        config = create_default_config()
        assert isinstance(config, TrainingConfig)
        assert config.cpu_only is True
        assert config.filter_discard_percent == 0.4
        assert config.max_memory_gb == 6.0
        assert config.seed == 42

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = create_default_config()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "experiment_name" in config_dict
        assert "filter_discard_percent" in config_dict
        assert config_dict["filter_discard_percent"] == 0.4

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "experiment_name": "test_exp",
            "seed": 123,
            "cpu_only": False,
            "filter_discard_percent": 0.5,
            "batch_size": 32,
        }
        config = TrainingConfig.from_dict(data)
        assert config.experiment_name == "test_exp"
        assert config.seed == 123
        assert config.cpu_only is False
        assert config.filter_discard_percent == 0.5

    def test_to_dict_roundtrip(self):
        """Test that to_dict and from_dict are inverses."""
        original = create_default_config()
        config_dict = original.to_dict()
        restored = TrainingConfig.from_dict(config_dict)
        assert original.experiment_name == restored.experiment_name
        assert original.filter_discard_percent == restored.filter_discard_percent


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_from_file(self):
        """Test loading config from a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            test_data = {
                "experiment_name": "loaded_test",
                "filter_discard_percent": 0.6,
                "batch_size": 8,
            }
            with open(config_path, "w") as f:
                yaml.dump(test_data, f)

            config = load_config(config_path)
            assert config.experiment_name == "loaded_test"
            assert config.filter_discard_percent == 0.6
            assert config.batch_size == 8

    def test_load_missing_file_uses_defaults(self):
        """Test that missing config file returns defaults."""
        config = load_config(Path("/nonexistent/path/config.yaml"))
        assert config.cpu_only is True
        assert config.filter_discard_percent == 0.4

    def test_load_partial_file_merges_defaults(self):
        """Test that partial config merges with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            test_data = {"learning_rate": 0.001}
            with open(config_path, "w") as f:
                yaml.dump(test_data, f)

            config = load_config(config_path)
            assert config.learning_rate == 0.001
            assert config.batch_size == DEFAULT_CONFIG["batch_size"]  # Default


class TestValidateConfigSchema:
    """Tests for config schema validation."""

    def test_valid_config(self):
        """Test that a valid config passes validation."""
        config = get_default_config()
        errors = validate_config_schema(config)
        assert len(errors) == 0

    def test_missing_required_key(self):
        """Test detection of missing required keys."""
        config = get_default_config()
        del config["seed"]
        errors = validate_config_schema(config)
        assert any("seed" in e for e in errors)

    def test_invalid_filter_discard_percent(self):
        """Test validation of filter_discard_percent range."""
        config = get_default_config()
        config["filter_discard_percent"] = 1.5
        errors = validate_config_schema(config)
        assert any("filter_discard_percent" in e for e in errors)

    def test_invalid_type(self):
        """Test detection of type mismatches."""
        config = get_default_config()
        config["batch_size"] = "not_an_int"
        errors = validate_config_schema(config)
        assert any("batch_size" in e for e in errors)


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_returns_training_config(self):
        """Test that function returns a TrainingConfig instance."""
        config = create_default_config()
        assert isinstance(config, TrainingConfig)

    def test_all_defaults_present(self):
        """Test that all default values are present."""
        config = create_default_config()
        cfg_dict = config.to_dict()
        for key, value in DEFAULT_CONFIG.items():
            assert cfg_dict[key] == value


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        config = get_default_config()
        assert isinstance(config, dict)

    def test_contains_required_keys(self):
        """Test that all required keys are present."""
        config = get_default_config()
        for key in REQUIRED_KEYS:
            assert key in config


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_and_load(self):
        """Test saving and loading a config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            original = create_default_config()
            original.filter_discard_percent = 0.75

            save_config(original, config_path)
            assert config_path.exists()

            loaded = load_config(config_path)
            assert loaded.filter_discard_percent == 0.75
            assert loaded.experiment_name == original.experiment_name

    def test_creates_parent_directories(self):
        """Test that save_config creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nested" / "dir" / "config.yaml"
            config = create_default_config()
            save_config(config, config_path)
            assert config_path.exists()


class TestGetFilterDiscardThreshold:
    """Tests for get_filter_discard_threshold function."""

    def test_default_threshold(self):
        """Test default threshold value."""
        threshold = get_filter_discard_threshold()
        assert threshold == 0.4

    def test_custom_threshold(self):
        """Test custom threshold from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            test_data = {"filter_discard_percent": 0.25}
            with open(config_path, "w") as f:
                yaml.dump(test_data, f)

            config = load_config(config_path)
            threshold = get_filter_discard_threshold(config)
            assert threshold == 0.25


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_default(self):
        """Test get_config returns default when no file exists."""
        config = get_config(Path("/nonexistent"))
        assert config.cpu_only is True

    def test_get_config_from_file(self):
        """Test get_config loads from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            test_data = {"seed": 999}
            with open(config_path, "w") as f:
                yaml.dump(test_data, f)

            config = get_config(config_path)
            assert config.seed == 999