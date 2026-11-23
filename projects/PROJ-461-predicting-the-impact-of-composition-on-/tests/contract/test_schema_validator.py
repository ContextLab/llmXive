"""
Contract tests for schema validation utilities.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from code.utils.schema_validator import (
    load_schema,
    validate_instance,
    load_and_validate,
    get_dataset_validator,
    get_model_output_validator,
    get_output_validator,
)


class TestLoadSchema:
    def test_load_yaml_schema(self, tmp_path):
        schema_content = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_content, f)

        validator = load_schema(schema_file)
        assert validator is not None
        assert list(validator.schema["properties"].keys()) == ["name"]

    def test_load_json_schema(self, tmp_path):
        schema_content = {
            "type": "object",
            "properties": {"value": {"type": "number"}},
            "required": ["value"],
        }
        schema_file = tmp_path / "schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema_content, f)

        validator = load_schema(schema_file)
        assert validator is not None
        assert validator.schema["properties"]["value"]["type"] == "number"

    def test_load_nonexistent_schema(self):
        with pytest.raises(FileNotFoundError):
            load_schema("nonexistent/path/schema.yaml")

    def test_load_invalid_yaml_schema(self, tmp_path):
        schema_file = tmp_path / "invalid.yaml"
        with open(schema_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ValueError):
            load_schema(schema_file)

    def test_load_invalid_json_schema(self, tmp_path):
        schema_file = tmp_path / "invalid.json"
        with open(schema_file, "w") as f:
            f.write('{ invalid json }')

        with pytest.raises(ValueError):
            load_schema(schema_file)

    def test_load_unsupported_format(self, tmp_path):
        schema_file = tmp_path / "schema.txt"
        schema_file.write_text("{}")

        with pytest.raises(ValueError):
            load_schema(schema_file)


class TestValidateInstance:
    def test_valid_instance(self, tmp_path):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)

        validator = load_schema(schema_file)
        instance = {"name": "test"}
        errors = validate_instance(validator, instance)
        assert errors == []

    def test_invalid_instance(self, tmp_path):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)

        validator = load_schema(schema_file)
        instance = {"name": 123}  # Should be string
        errors = validate_instance(validator, instance)
        assert len(errors) > 0
        assert any("string" in err for err in errors)

    def test_missing_required_field(self, tmp_path):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)

        validator = load_schema(schema_file)
        instance = {}
        errors = validate_instance(validator, instance)
        assert len(errors) > 0
        assert any("name" in err for err in errors)


class TestLoadAndValidate:
    def test_successful_validation(self, tmp_path):
        schema_content = {
            "type": "object",
            "properties": {"value": {"type": "number"}},
            "required": ["value"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_content, f)

        data_content = {"value": 42.5}
        data_file = tmp_path / "data.json"
        with open(data_file, "w") as f:
            json.dump(data_content, f)

        is_valid, errors = load_and_validate(schema_file, data_file)
        assert is_valid
        assert errors == []

    def test_data_file_not_found(self, tmp_path):
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text("{}")

        is_valid, errors = load_and_validate(schema_file, tmp_path / "missing.json")
        assert not is_valid
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_invalid_json_data(self, tmp_path):
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text("{}")

        data_file = tmp_path / "data.json"
        data_file.write_text("{ invalid json }")

        is_valid, errors = load_and_validate(schema_file, data_file)
        assert not is_valid
        assert len(errors) == 1
        assert "Failed to parse" in errors[0]

    def test_validation_fails(self, tmp_path):
        schema_content = {
            "type": "object",
            "properties": {"value": {"type": "number"}},
            "required": ["value"],
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema_content, f)

        data_content = {"value": "not a number"}
        data_file = tmp_path / "data.json"
        with open(data_file, "w") as f:
            json.dump(data_content, f)

        is_valid, errors = load_and_validate(schema_file, data_file)
        assert not is_valid
        assert len(errors) > 0


class TestConvenienceWrappers:
    def test_get_dataset_validator_exists(self):
        # This will raise FileNotFoundError if the schema doesn't exist,
        # which is the expected behavior for missing contracts.
        # If it exists, it should return a validator.
        try:
            validator = get_dataset_validator()
            assert validator is not None
        except FileNotFoundError:
            # Expected if contracts/ directory or schema is missing
            pytest.skip("contracts/dataset.schema.yaml not found")

    def test_get_model_output_validator_exists(self):
        try:
            validator = get_model_output_validator()
            assert validator is not None
        except FileNotFoundError:
            pytest.skip("contracts/model_output.schema.yaml not found")

    def test_get_output_validator_exists(self):
        try:
            validator = get_output_validator()
            assert validator is not None
        except FileNotFoundError:
            pytest.skip("contracts/output.schema.yaml not found")