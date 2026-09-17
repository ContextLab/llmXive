"""
Unit tests for schema validation logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from data.schema_validator import (
    load_schema,
    validate_type,
    validate_item,
    validate_json_file,
    validate_yaml_file,
    DataFetchError
)


class TestValidateType:
    def test_valid_string(self):
        validate_type("hello", "string", "test.field")

    def test_invalid_string(self):
        with pytest.raises(ValueError, match="expected string"):
            validate_type(123, "string", "test.field")

    def test_valid_integer(self):
        validate_type(42, "integer", "test.field")

    def test_invalid_integer_bool(self):
        # bool is subclass of int, must be explicitly rejected for integer type
        with pytest.raises(ValueError, match="expected integer"):
            validate_type(True, "integer", "test.field")

    def test_valid_number(self):
        validate_type(3.14, "number", "test.field")
        validate_type(10, "number", "test.field")

    def test_invalid_number_bool(self):
        with pytest.raises(ValueError, match="expected number"):
            validate_type(True, "number", "test.field")

    def test_valid_boolean(self):
        validate_type(True, "boolean", "test.field")
        validate_type(False, "boolean", "test.field")

    def test_invalid_boolean(self):
        with pytest.raises(ValueError, match="expected boolean"):
            validate_type("true", "boolean", "test.field")

    def test_valid_array(self):
        validate_type([1, 2, 3], "array", "test.field")

    def test_invalid_array(self):
        with pytest.raises(ValueError, match="expected array"):
            validate_type({"key": "value"}, "array", "test.field")

    def test_valid_object(self):
        validate_type({"key": "value"}, "object", "test.field")

    def test_invalid_object(self):
        with pytest.raises(ValueError, match="expected object"):
            validate_type([], "object", "test.field")

    def test_valid_null(self):
        validate_type(None, "null", "test.field")

    def test_invalid_null(self):
        with pytest.raises(ValueError, match="expected null"):
            validate_type("not null", "null", "test.field")


class TestValidateItem:
    def test_validate_simple_object(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        data = {"name": "Alice", "age": 30}
        validate_item(data, schema, "root")

    def test_validate_missing_required(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        data = {}
        with pytest.raises(ValueError, match="Missing required field"):
            validate_item(data, schema, "root")

    def test_validate_nested_object(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
        data = {"user": {"id": 123}}
        validate_item(data, schema, "root")

    def test_validate_array_items(self):
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        data = ["a", "b", "c"]
        validate_item(data, schema, "root")

    def test_validate_array_invalid_item(self):
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        data = ["a", 123, "c"]
        with pytest.raises(ValueError, match="expected string"):
            validate_item(data, schema, "root")

    def test_validate_format_email(self):
        schema = {
            "type": "string",
            "format": "email"
        }
        validate_item("user@example.com", schema, "root")

    def test_validate_format_email_invalid(self):
        schema = {
            "type": "string",
            "format": "email"
        }
        with pytest.raises(ValueError, match="not a valid email"):
            validate_item("not-an-email", schema, "root")

    def test_validate_format_uri(self):
        schema = {
            "type": "string",
            "format": "uri"
        }
        validate_item("https://example.com", schema, "root")

    def test_validate_format_uri_invalid(self):
        schema = {
            "type": "string",
            "format": "uri"
        }
        with pytest.raises(ValueError, match="not a valid URI"):
            validate_item("ftp://example.com", schema, "root") # Invalid per simple check


class TestValidateJsonFile:
    @pytest.fixture
    def temp_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json.dumps({"name": "Test", "value": 123}))
            path = f.name
        yield path
        Path(path).unlink()

    @pytest.fixture
    def temp_schema_file(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            },
            "required": ["name"]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".schema.yaml", delete=False) as f:
            yaml.dump(schema, f)
            path = f.name
        yield path
        Path(path).unlink()

    def test_valid_json_file(self, temp_json_file, temp_schema_file):
        # Mock load_schema to use temp schema
        with patch("data.schema_validator.CONTRACTS_DIR", Path(temp_schema_file).parent):
            with patch("data.schema_validator.load_schema") as mock_load:
                mock_load.return_value = yaml.safe_load(open(temp_schema_file))
                result = validate_json_file(temp_json_file, "dummy.schema.yaml")
                assert result is True

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            validate_json_file("/nonexistent/path/file.json", "schema.yaml")

    def test_invalid_json_content(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                validate_json_file(path, "schema.yaml")
        finally:
            Path(path).unlink()


class TestValidateYamlFile:
    @pytest.fixture
    def temp_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: Test\nvalue: 123")
            path = f.name
        yield path
        Path(path).unlink()

    def test_valid_yaml_file(self, temp_yaml_file):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            },
            "required": ["name"]
        }
        with patch("data.schema_validator.load_schema") as mock_load:
            mock_load.return_value = schema
            result = validate_yaml_file(temp_yaml_file, "dummy.schema.yaml")
            assert result is True

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            validate_yaml_file("/nonexistent/path/file.yaml", "schema.yaml")

    def test_invalid_yaml_content(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: [unclosed")
            path = f.name
        try:
            with pytest.raises(yaml.YAMLError):
                validate_yaml_file(path, "schema.yaml")
        finally:
            Path(path).unlink()