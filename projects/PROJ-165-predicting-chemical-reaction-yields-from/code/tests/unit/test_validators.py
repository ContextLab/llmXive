"""
Unit tests for schema validation helpers in src.utils.validators.
"""
import json
import yaml
import tempfile
import os
from pathlib import Path
import pytest

from src.utils.validators import (
    ValidationError,
    load_yaml,
    load_json,
    validate_type,
    validate_required_fields,
    validate_range,
    validate_schema,
    validate_config_file
)


class TestLoadYAML:
    def test_load_valid_yaml(self, tmp_path):
        """Test loading a valid YAML file."""
        yaml_content = """
        key1: value1
        key2: 123
        key3:
          nested: true
        """
        file_path = tmp_path / "config.yaml"
        file_path.write_text(yaml_content)

        result = load_yaml(file_path)
        assert result["key1"] == "value1"
        assert result["key2"] == 123
        assert result["key3"]["nested"] is True

    def test_load_empty_yaml(self, tmp_path):
        """Test loading an empty YAML file returns empty dict."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("")

        result = load_yaml(file_path)
        assert result == {}

    def test_load_missing_yaml(self, tmp_path):
        """Test that loading a missing file raises ValidationError."""
        file_path = tmp_path / "missing.yaml"

        with pytest.raises(ValidationError) as exc_info:
            load_yaml(file_path)

        assert "not found" in str(exc_info.value)

    def test_load_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises ValidationError."""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text("key: [unclosed")

        with pytest.raises(ValidationError):
            load_yaml(file_path)


class TestLoadJSON:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        json_content = {
            "key1": "value1",
            "key2": 123,
            "key3": {"nested": True}
        }
        file_path = tmp_path / "config.json"
        file_path.write_text(json.dumps(json_content))

        result = load_json(file_path)
        assert result["key1"] == "value1"
        assert result["key2"] == 123
        assert result["key3"]["nested"] is True

    def test_load_missing_json(self, tmp_path):
        """Test that loading a missing file raises ValidationError."""
        file_path = tmp_path / "missing.json"

        with pytest.raises(ValidationError) as exc_info:
            load_json(file_path)

        assert "not found" in str(exc_info.value)

    def test_load_invalid_json(self, tmp_path):
        """Test that invalid JSON raises ValidationError."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{key: unquoted}")

        with pytest.raises(ValidationError):
            load_json(file_path)


class TestValidateType:
    def test_valid_type(self):
        """Test that valid type passes."""
        validate_type(123, int, "test_field")
        validate_type("string", str, "test_field")
        validate_type(3.14, float, "test_field")

    def test_invalid_type(self):
        """Test that invalid type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_type("string", int, "test_field")

        assert "must be of type int" in str(exc_info.value)


class TestValidateRequiredFields:
    def test_all_present(self):
        """Test validation when all required fields are present."""
        data = {"a": 1, "b": 2, "c": 3}
        validate_required_fields(data, ["a", "b"], "TestContext")

    def test_missing_fields(self):
        """Test validation fails when required fields are missing."""
        data = {"a": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, ["a", "b", "c"], "TestContext")

        assert "Missing required fields" in str(exc_info.value)
        assert "b" in str(exc_info.value)
        assert "c" in str(exc_info.value)


class TestValidateRange:
    def test_within_range(self):
        """Test value within bounds passes."""
        validate_range(5, min_val=0, max_val=10, field_name="test")
        validate_range(0, min_val=0, max_val=10, field_name="test")
        validate_range(10, min_val=0, max_val=10, field_name="test")

    def test_below_min(self):
        """Test value below minimum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_range(-1, min_val=0, max_val=10, field_name="test")

        assert "below minimum" in str(exc_info.value)

    def test_above_max(self):
        """Test value above maximum raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_range(11, min_val=0, max_val=10, field_name="test")

        assert "above maximum" in str(exc_info.value)

    def test_non_numeric(self):
        """Test non-numeric value raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_range("string", min_val=0, max_val=10, field_name="test")

        assert "must be numeric" in str(exc_info.value)


class TestValidateSchema:
    def test_valid_schema(self):
        """Test data matching schema passes."""
        data = {
            "name": "test",
            "count": 5,
            "enabled": True
        }
        schema = {
            "name": {"type": str, "required": True},
            "count": {"type": int, "required": True, "min": 0, "max": 100},
            "enabled": {"type": bool, "required": False}
        }
        validate_schema(data, schema)

    def test_missing_required(self):
        """Test missing required field fails."""
        data = {"count": 5}
        schema = {
            "name": {"type": str, "required": True},
            "count": {"type": int, "required": True}
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)

        assert "Required field 'name' is missing" in str(exc_info.value)

    def test_type_mismatch(self):
        """Test type mismatch fails."""
        data = {"count": "five"}
        schema = {
            "count": {"type": int, "required": True}
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)

        assert "must be of type int" in str(exc_info.value)

    def test_range_violation(self):
        """Test range violation fails."""
        data = {"count": 150}
        schema = {
            "count": {"type": int, "required": True, "min": 0, "max": 100}
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)

        assert "above maximum" in str(exc_info.value)

    def test_allowed_values(self):
        """Test allowed values constraint."""
        schema = {
            "mode": {"type": str, "required": True, "allowed_values": ["train", "eval"]}
        }

        # Valid
        validate_schema({"mode": "train"}, schema)

        # Invalid
        with pytest.raises(ValidationError) as exc_info:
            validate_schema({"mode": "invalid"}, schema)

        assert "not in allowed values" in str(exc_info.value)


class TestValidateConfigFile:
    def test_validate_yaml_config(self, tmp_path):
        """Test validating a YAML config file."""
        config_content = """
        learning_rate: 0.001
        batch_size: 32
        epochs: 10
        """
        file_path = tmp_path / "config.yaml"
        file_path.write_text(config_content)

        schema = {
            "learning_rate": {"type": float, "required": True, "min": 0.0, "max": 1.0},
            "batch_size": {"type": int, "required": True, "min": 1},
            "epochs": {"type": int, "required": True, "min": 1}
        }

        result = validate_config_file(file_path, schema)
        assert result["learning_rate"] == 0.001
        assert result["batch_size"] == 32
        assert result["epochs"] == 10

    def test_validate_json_config(self, tmp_path):
        """Test validating a JSON config file."""
        config_content = {
            "learning_rate": 0.001,
            "batch_size": 32
        }
        file_path = tmp_path / "config.json"
        file_path.write_text(json.dumps(config_content))

        schema = {
            "learning_rate": {"type": float, "required": True},
            "batch_size": {"type": int, "required": True}
        }

        result = validate_config_file(file_path, schema)
        assert result["learning_rate"] == 0.001
        assert result["batch_size"] == 32

    def test_validate_missing_file(self, tmp_path):
        """Test validation fails for missing file."""
        file_path = tmp_path / "missing.yaml"
        schema = {"key": {"type": str, "required": True}}

        with pytest.raises(ValidationError):
            validate_config_file(file_path, schema)

    def test_validate_invalid_schema(self, tmp_path):
        """Test validation fails if data doesn't match schema."""
        config_content = """
        learning_rate: "not_a_float"
        """
        file_path = tmp_path / "config.yaml"
        file_path.write_text(config_content)

        schema = {
            "learning_rate": {"type": float, "required": True}
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_config_file(file_path, schema)

        assert "must be of type float" in str(exc_info.value)