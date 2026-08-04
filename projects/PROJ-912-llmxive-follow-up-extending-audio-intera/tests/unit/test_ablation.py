"""
Unit tests for ablation configuration parsing in code/analysis/ablation.py.

These tests verify that the ablation configuration parser correctly:
1. Parses valid configuration dictionaries
2. Handles missing optional fields with defaults
3. Validates required fields and raises appropriate errors
4. Supports multiple configuration profiles
5. Validates parameter types and ranges
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

# Import the module under test
# Note: We need to add the code directory to sys.path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.ablation import (
    parse_ablation_config,
    validate_ablation_config,
    get_default_ablation_config,
    AblationConfig,
    parse_config_from_file,
    load_multiple_configs
)
from utils.logger import ConfigurationError


class TestParseAblationConfig:
    """Tests for the parse_ablation_config function."""

    def test_parse_minimal_valid_config(self):
        """Test parsing a minimal valid configuration."""
        config_dict = {
            "freeze_attention": True,
            "prune_ffn": False
        }

        result = parse_ablation_config(config_dict)

        assert isinstance(result, AblationConfig)
        assert result.freeze_attention is True
        assert result.prune_ffn is False
        assert result.config_id == "default"
        assert result.description == "Minimal config"

    def test_parse_full_config(self):
        """Test parsing a full configuration with all fields."""
        config_dict = {
            "config_id": "test_config_1",
            "description": "Test configuration with all fields",
            "freeze_attention": True,
            "freeze_attention_layers": [0, 1, 2],
            "prune_ffn": True,
            "prune_ffn_layers": [3, 4],
            "prune_ratio": 0.5,
            "random_seed": 42
        }

        result = parse_ablation_config(config_dict)

        assert isinstance(result, AblationConfig)
        assert result.config_id == "test_config_1"
        assert result.description == "Test configuration with all fields"
        assert result.freeze_attention is True
        assert result.freeze_attention_layers == [0, 1, 2]
        assert result.prune_ffn is True
        assert result.prune_ffn_layers == [3, 4]
        assert result.prune_ratio == 0.5
        assert result.random_seed == 42

    def test_parse_with_defaults(self):
        """Test that missing optional fields use defaults."""
        config_dict = {
            "freeze_attention": False,
            "prune_ffn": False
        }

        result = parse_ablation_config(config_dict)

        # Check defaults
        assert result.config_id == "default"
        assert result.description == "Default configuration"
        assert result.freeze_attention_layers == []
        assert result.prune_ffn_layers == []
        assert result.prune_ratio == 0.0
        assert result.random_seed == 42

    def test_parse_invalid_type_for_freeze_attention(self):
        """Test that invalid type for freeze_attention raises error."""
        config_dict = {
            "freeze_attention": "true",  # Should be boolean
            "prune_ffn": False
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)

    def test_parse_invalid_type_for_prune_ratio(self):
        """Test that invalid type for prune_ratio raises error."""
        config_dict = {
            "freeze_attention": False,
            "prune_ffn": False,
            "prune_ratio": "0.5"  # Should be float
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)

    def test_parse_prune_ratio_out_of_range(self):
        """Test that prune_ratio outside [0, 1] raises error."""
        config_dict = {
            "freeze_attention": False,
            "prune_ffn": False,
            "prune_ratio": 1.5  # Out of range
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)

    def test_parse_negative_prune_ratio(self):
        """Test that negative prune_ratio raises error."""
        config_dict = {
            "freeze_attention": False,
            "prune_ffn": False,
            "prune_ratio": -0.1  # Negative
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)

    def test_parse_invalid_layer_indices(self):
        """Test that negative layer indices raise error."""
        config_dict = {
            "freeze_attention": True,
            "freeze_attention_layers": [-1, 0, 1],
            "prune_ffn": False
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)

    def test_parse_non_integer_layer_indices(self):
        """Test that non-integer layer indices raise error."""
        config_dict = {
            "freeze_attention": True,
            "freeze_attention_layers": [0, 1.5, 2],
            "prune_ffn": False
        }

        with pytest.raises(ConfigurationError):
            parse_ablation_config(config_dict)


class TestValidateAblationConfig:
    """Tests for the validate_ablation_config function."""

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        config_dict = {
            "config_id": "valid_config",
            "freeze_attention": True,
            "prune_ffn": True,
            "prune_ratio": 0.3
        }

        is_valid, errors = validate_ablation_config(config_dict)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_required_field(self):
        """Test validation when required field is missing."""
        config_dict = {
            "freeze_attention": True
            # Missing prune_ffn
        }

        is_valid, errors = validate_ablation_config(config_dict)

        assert is_valid is False
        assert len(errors) > 0
        assert any("prune_ffn" in error for error in errors)

    def test_validate_invalid_structure(self):
        """Test validation of invalid structure."""
        config_dict = "not a dictionary"

        is_valid, errors = validate_ablation_config(config_dict)

        assert is_valid is False
        assert len(errors) > 0


class TestGetDefaultAblationConfig:
    """Tests for the get_default_ablation_config function."""

    def test_default_config_structure(self):
        """Test that default config has expected structure."""
        config = get_default_ablation_config()

        assert isinstance(config, dict)
        assert "config_id" in config
        assert "freeze_attention" in config
        assert "prune_ffn" in config
        assert "prune_ratio" in config

    def test_default_config_values(self):
        """Test that default config has correct default values."""
        config = get_default_ablation_config()

        assert config["config_id"] == "default"
        assert config["freeze_attention"] is False
        assert config["prune_ffn"] is False
        assert config["prune_ratio"] == 0.0
        assert config["random_seed"] == 42


class TestParseConfigFromFile:
    """Tests for the parse_config_from_file function."""

    def test_parse_from_json_file(self, tmp_path):
        """Test parsing configuration from a JSON file."""
        config_dict = {
            "config_id": "file_config",
            "freeze_attention": True,
            "prune_ffn": False,
            "description": "Config loaded from file"
        }

        config_file = tmp_path / "ablation_config.json"
        config_file.write_text(json.dumps(config_dict))

        result = parse_config_from_file(str(config_file))

        assert isinstance(result, AblationConfig)
        assert result.config_id == "file_config"
        assert result.freeze_attention is True

    def test_parse_from_nonexistent_file(self, tmp_path):
        """Test that parsing from non-existent file raises error."""
        non_existent_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            parse_config_from_file(str(non_existent_file))

    def test_parse_invalid_json_file(self, tmp_path):
        """Test that parsing invalid JSON file raises error."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        with pytest.raises((json.JSONDecodeError, ConfigurationError)):
            parse_config_from_file(str(config_file))


class TestLoadMultipleConfigs:
    """Tests for the load_multiple_configs function."""

    def test_load_multiple_configs_from_list(self, tmp_path):
        """Test loading multiple configurations from a list of files."""
        configs = [
            {"config_id": "config1", "freeze_attention": True, "prune_ffn": False},
            {"config_id": "config2", "freeze_attention": False, "prune_ffn": True},
            {"config_id": "config3", "freeze_attention": True, "prune_ffn": True}
        ]

        config_files = []
        for i, config in enumerate(configs):
          config_file = tmp_path / f"ablation_config_{i}.json"
          config_file.write_text(json.dumps(config))
          config_files.append(str(config_file))

        results = load_multiple_configs(config_files)

        assert len(results) == 3
        assert all(isinstance(r, AblationConfig) for r in results)
        assert results[0].config_id == "config1"
        assert results[1].config_id == "config2"
        assert results[2].config_id == "config3"

    def test_load_empty_config_list(self):
        """Test loading from an empty list."""
        results = load_multiple_configs([])

        assert len(results) == 0

    def test_load_with_one_invalid_config(self, tmp_path):
        """Test that loading fails if one config is invalid."""
        valid_config = {"config_id": "valid", "freeze_attention": True, "prune_ffn": False}
        invalid_config = {"config_id": "invalid", "prune_ratio": -0.5}  # Invalid

        valid_file = tmp_path / "valid.json"
        valid_file.write_text(json.dumps(valid_config))

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text(json.dumps(invalid_config))

        with pytest.raises(ConfigurationError):
            load_multiple_configs([str(valid_file), str(invalid_file)])


class TestAblationConfigDataclass:
    """Tests for the AblationConfig dataclass itself."""

    def test_ablation_config_creation(self):
        """Test creating an AblationConfig instance directly."""
        config = AblationConfig(
            config_id="direct_test",
            description="Direct creation test",
            freeze_attention=True,
            freeze_attention_layers=[0, 1],
            prune_ffn=True,
            prune_ffn_layers=[2],
            prune_ratio=0.3,
            random_seed=123
        )

        assert config.config_id == "direct_test"
        assert config.description == "Direct creation test"
        assert config.freeze_attention is True
        assert config.freeze_attention_layers == [0, 1]
        assert config.prune_ffn is True
        assert config.prune_ffn_layers == [2]
        assert config.prune_ratio == 0.3
        assert config.random_seed == 123

    def test_ablation_config_repr(self):
        """Test that AblationConfig has a meaningful string representation."""
        config = AblationConfig(
            config_id="repr_test",
            freeze_attention=True,
            prune_ffn=False
        )

        repr_str = repr(config)
        assert "repr_test" in repr_str
        assert "freeze_attention=True" in repr_str