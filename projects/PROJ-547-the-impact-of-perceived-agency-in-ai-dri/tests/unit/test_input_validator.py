"""
Unit tests for the input_validator module.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from utils.error_handler import PipelineError
from utils.input_validator import (
    validate_file_type,
    validate_json_schema,
    validate_yaml_file,
)


class TestValidateFileType:
    def test_valid_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            f.write(b"col1,col2\n1,2")
            path = Path(f.name)

        try:
            assert validate_file_type(path, ["text/csv"]) is True
        finally:
            path.unlink()

    def test_invalid_type(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"text")
            path = Path(f.name)

        try:
            with pytest.raises(PipelineError) as exc_info:
                validate_file_type(path, ["text/csv"])
            assert "Invalid file type" in str(exc_info.value)
        finally:
            path.unlink()

    def test_file_not_found(self):
        path = Path("/nonexistent/file.csv")
        with pytest.raises(PipelineError) as exc_info:
            validate_file_type(path, ["text/csv"])
        assert "File not found" in str(exc_info.value)


class TestValidateJsonSchema:
    def test_valid_schema(self):
        data = {"name": "Alice", "age": 30}
        schema = {
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
            },
        }
        assert validate_json_schema(data, schema) is True

    def test_missing_required(self):
        data = {"name": "Alice"}
        schema = {"required": ["name", "age"]}
        with pytest.raises(PipelineError) as exc_info:
            validate_json_schema(data, schema)
        assert "Missing required field" in str(exc_info.value)

    def test_wrong_type(self):
        data = {"name": 123}
        schema = {
            "properties": {"name": {"type": "string"}},
        }
        with pytest.raises(PipelineError) as exc_info:
            validate_json_schema(data, schema)
        assert "must be a string" in str(exc_info.value)


class TestValidateYamlFile:
    def test_valid_yaml(self):
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w"
        ) as f:
            yaml.dump({"key": "value"}, f)
            path = Path(f.name)

        try:
            result = validate_yaml_file(path)
            assert result == {"key": "value"}
        finally:
            path.unlink()

    def test_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w"
        ) as f:
            f.write("invalid: yaml: content: [")
            path = Path(f.name)

        try:
            with pytest.raises(PipelineError) as exc_info:
                validate_yaml_file(path)
            assert "Invalid YAML" in str(exc_info.value)
        finally:
            path.unlink()

    def test_file_not_found(self):
        path = Path("/nonexistent/file.yaml")
        with pytest.raises(PipelineError) as exc_info:
            validate_yaml_file(path)
        assert "YAML file not found" in str(exc_info.value)
