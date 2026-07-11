"""
Unit tests for the configuration loader module.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

import sys
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config.loader import (
    load_config,
    validate_config,
    get_config_value,
    ConfigError,
)


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_data = {
            "seeds": {"default": 42},
            "thresholds": {"alpha": 0.05},
            "batch_size_start": 50,
            "timeout_limits": {"task": 300, "overall": 3600},
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loaded_config = load_config(str(config_file))

        assert loaded_config == config_data

    def test_config_file_not_found(self):
        """Test that ConfigError is raised when file doesn't exist."""
        with pytest.raises(ConfigError, match="Configuration file not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_empty_config_file(self, tmp_path):
        """Test that ConfigError is raised for empty YAML file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ConfigError, match="Configuration file is empty"):
            load_config(str(config_file))

    def test_null_config_file(self, tmp_path):
        """Test that ConfigError is raised for null YAML content."""
        config_file = tmp_path / "null.yaml"
        config_file.write_text("null")

        with pytest.raises(ConfigError, match="Configuration file is empty"):
            load_config(str(config_file))

    def test_invalid_yaml(self, tmp_path):
        """Test that ConfigError is raised for invalid YAML syntax."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigError, match="Failed to parse YAML"):
            load_config(str(config_file))

    def test_non_dict_config(self, tmp_path):
        """Test that ConfigError is raised when config is not a dict."""
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- item1\n- item2")

        with pytest.raises(ConfigError, match="Configuration must be a YAML mapping"):
            load_config(str(config_file))


class TestValidateConfig:
    """Tests for the validate_config function."""

    def test_valid_config(self):
        """Test validation passes for valid config."""
        config = {
            "seeds": {"default": 42},
            "thresholds": {"alpha": 0.05},
            "batch_size_start": 50,
            "timeout_limits": {"task": 300, "overall": 3600},
        }

        # Should not raise
        validate_config(config)

    def test_missing_top_level_key(self):
        """Test validation fails when top-level key is missing."""
        config = {
            "seeds": {"default": 42},
            "thresholds": {"alpha": 0.05},
            "batch_size_start": 50,
            # Missing timeout_limits
        }

        with pytest.raises(ConfigError, match="Missing required configuration keys"):
            validate_config(config)

    def test_wrong_type_top_level(self):
        """Test validation fails when top-level key has wrong type."""
        config = {
            "seeds": {"default": 42},
            "thresholds": {"alpha": 0.05},
            "batch_size_start": "50",  # Should be int
            "timeout_limits": {"task": 300, "overall": 3600},
        }

        with pytest.raises(ConfigError, match="Key 'batch_size_start' must be of type int"):
            validate_config(config)

    def test_missing_nested_key(self):
        """Test validation fails when nested key is missing."""
        config = {
            "seeds": {},  # Missing 'default'
            "thresholds": {"alpha": 0.05},
            "batch_size_start": 50,
            "timeout_limits": {"task": 300, "overall": 3600},
        }

        with pytest.raises(ConfigError, match="Missing required nested key 'seeds.default'"):
            validate_config(config)

    def test_wrong_type_nested_key(self):
        """Test validation fails when nested key has wrong type."""
        config = {
            "seeds": {"default": "42"},  # Should be int
            "thresholds": {"alpha": 0.05},
            "batch_size_start": 50,
            "timeout_limits": {"task": 300, "overall": 3600},
        }

        with pytest.raises(ConfigError, match="Key 'seeds.default' must be of type int"):
            validate_config(config)


class TestGetConfigValue:
    """Tests for the get_config_value function."""

    def test_get_existing_value(self):
        """Test retrieving an existing value."""
        config = {
            "seeds": {"default": 42},
            "thresholds": {"alpha": 0.05},
        }

        assert get_config_value(config, "seeds.default") == 42
        assert get_config_value(config, "thresholds.alpha") == 0.05

    def test_get_nonexistent_value(self):
        """Test retrieving a nonexistent value returns default."""
        config = {
            "seeds": {"default": 42},
        }

        assert get_config_value(config, "seeds.missing") is None
        assert get_config_value(config, "seeds.missing", default=99) == 99
        assert get_config_value(config, "nonexistent.key") is None

    def test_get_deeply_nested_value(self):
        """Test retrieving a deeply nested value."""
        config = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }

        assert get_config_value(config, "level1.level2.level3") == "deep_value"

    def test_get_value_with_mixed_types(self):
        """Test retrieving values of different types."""
        config = {
            "int_val": 42,
            "float_val": 3.14,
            "str_val": "hello",
            "bool_val": True,
            "list_val": [1, 2, 3],
        }

        assert get_config_value(config, "int_val") == 42
        assert get_config_value(config, "float_val") == 3.14
        assert get_config_value(config, "str_val") == "hello"
        assert get_config_value(config, "bool_val") is True
        assert get_config_value(config, "list_val") == [1, 2, 3]