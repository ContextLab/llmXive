"""
Unit tests for schema validation helpers in src/utils/validators.py.
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
        content = "name: test\nvalue: 123\n"
        file_path = tmp_path / "config.yaml"
        file_path.write_text(content)
        
        result = load_yaml(file_path)
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_load_missing_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            load_yaml(file_path)

    def test_load_malformed_yaml(self, tmp_path):
        content = "invalid: yaml: content: ["
        file_path = tmp_path / "bad.yaml"
        file_path.write_text(content)
        
        with pytest.raises(yaml.YAMLError):
            load_yaml(file_path)


class TestLoadJSON:
    def test_load_valid_json(self, tmp_path):
        content = '{"name": "test", "value": 456}'
        file_path = tmp_path / "config.json"
        file_path.write_text(content)
        
        result = load_json(file_path)
        assert result["name"] == "test"
        assert result["value"] == 456

    def test_load_missing_file(self, tmp_path):
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_json(file_path)

    def test_load_malformed_json(self, tmp_path):
        content = '{"invalid": json}'
        file_path = tmp_path / "bad.json"
        file_path.write_text(content)
        
        with pytest.raises(json.JSONDecodeError):
            load_json(file_path)


class TestValidateType:
    def test_valid_type(self):
        validate_type(123, int, "test_field")  # Should not raise
        validate_type("string", str, "test_field")
        validate_type(1.5, float, "test_field")

    def test_invalid_type(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_type("123", int, "test_field")
        assert "int" in str(exc_info.value)
        assert "str" in str(exc_info.value)


class TestValidateRequiredFields:
    def test_all_present(self):
        data = {"a": 1, "b": 2, "c": 3}
        validate_required_fields(data, ["a", "b"])  # Should not raise

    def test_missing_fields(self):
        data = {"a": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate_required_fields(data, ["a", "b", "c"])
        assert "b" in str(exc_info.value)
        assert "c" in str(exc_info.value)


class TestValidateRange:
    def test_within_range(self):
        validate_range(5, min_val=0, max_val=10, field_name="test")
        validate_range(0, min_val=0, max_val=10, field_name="test")
        validate_range(10, min_val=0, max_val=10, field_name="test")

    def test_below_min(self):
        with pytest.raises(ValidationError):
            validate_range(-1, min_val=0, max_val=10, field_name="test")

    def test_above_max(self):
        with pytest.raises(ValidationError):
            validate_range(11, min_val=0, max_val=10, field_name="test")

    def test_no_bounds(self):
        validate_range(999, field_name="test")  # No min/max specified


class TestValidateSchema:
    def test_valid_schema(self):
        data = {
            "learning_rate": 0.001,
            "epochs": 10,
            "optimizer": "adam"
        }
        schema = {
            "learning_rate": {"type": float, "required": True, "min": 0, "max": 1},
            "epochs": {"type": int, "required": True, "min": 1},
            "optimizer": {"type": str, "required": True, "allowed": ["adam", "sgd"]}
        }
        validate_schema(data, schema, "test_schema")  # Should not raise

    def test_missing_required(self):
        data = {"learning_rate": 0.001}
        schema = {
            "learning_rate": {"type": float, "required": True},
            "epochs": {"type": int, "required": True}
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema, "test_schema")
        assert "epochs" in str(exc_info.value)

    def test_wrong_type(self):
        data = {"learning_rate": "0.001"}
        schema = {
            "learning_rate": {"type": float, "required": True}
        }
        with pytest.raises(ValidationError):
            validate_schema(data, schema, "test_schema")

    def test_out_of_range(self):
        data = {"learning_rate": 1.5}
        schema = {
            "learning_rate": {"type": float, "required": True, "min": 0, "max": 1}
        }
        with pytest.raises(ValidationError):
            validate_schema(data, schema, "test_schema")

    def test_invalid_allowed_value(self):
        data = {"optimizer": "rmsprop"}
        schema = {
            "optimizer": {"type": str, "required": True, "allowed": ["adam", "sgd"]}
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema, "test_schema")
        assert "rmsprop" in str(exc_info.value)


class TestValidateConfigFile:
    def test_valid_yaml_config(self, tmp_path):
        content = "learning_rate: 0.001\nepochs: 10\n"
        file_path = tmp_path / "config.yaml"
        file_path.write_text(content)
        
        schema = {
            "learning_rate": {"type": float, "required": True},
            "epochs": {"type": int, "required": True}
        }
        
        result = validate_config_file(file_path, schema, "yaml")
        assert result["learning_rate"] == 0.001
        assert result["epochs"] == 10

    def test_valid_json_config(self, tmp_path):
        content = '{"learning_rate": 0.001, "epochs": 10}'
        file_path = tmp_path / "config.json"
        file_path.write_text(content)
        
        schema = {
            "learning_rate": {"type": float, "required": True},
            "epochs": {"type": int, "required": True}
        }
        
        result = validate_config_file(file_path, schema, "json")
        assert result["learning_rate"] == 0.001
        assert result["epochs"] == 10

    def test_missing_file(self, tmp_path):
        file_path = tmp_path / "missing.yaml"
        schema = {"field": {"type": str, "required": True}}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config_file(file_path, schema, "yaml")
        assert "not found" in str(exc_info.value).lower()

    def test_validation_error_in_file(self, tmp_path):
        content = "learning_rate: high_value\n"
        file_path = tmp_path / "config.yaml"
        file_path.write_text(content)
        
        schema = {
            "learning_rate": {"type": float, "required": True}
        }
        
        with pytest.raises(ValidationError):
            validate_config_file(file_path, schema, "yaml")

    def test_non_dict_json(self, tmp_path):
        content = '["array", "not", "object"]'
        file_path = tmp_path / "config.json"
        file_path.write_text(content)
        
        schema = {}
        with pytest.raises(ValidationError) as exc_info:
            validate_config_file(file_path, schema, "json")
        assert "dictionary" in str(exc_info.value).lower() or "object" in str(exc_info.value).lower()