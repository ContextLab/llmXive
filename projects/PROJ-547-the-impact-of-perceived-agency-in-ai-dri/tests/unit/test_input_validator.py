"""
Unit tests for the input validation utilities.
"""
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from utils.error_handler import PipelineError
from utils.input_validator import (
    validate_file_path,
    validate_file_extension,
    validate_json_schema,
    load_and_validate_yaml,
)


def test_validate_file_path_missing():
    """Test validation of a missing required file."""
    path = Path("/nonexistent/file.txt")
    with pytest.raises(PipelineError) as exc_info:
        validate_file_path(path, required=True)
    assert "Required file not found" in str(exc_info.value.message)


def test_validate_file_path_not_file():
    """Test validation of a path that is a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        with pytest.raises(PipelineError) as exc_info:
            validate_file_path(path, required=True)
        assert "not a file" in str(exc_info.value.message)


def test_validate_file_extension_invalid():
    """Test validation of a file with an invalid extension."""
    path = Path("file.txt")
    with pytest.raises(PipelineError) as exc_info:
        validate_file_extension(path, allowed_extensions=[".csv", ".json"])
    assert "Invalid file extension" in str(exc_info.value.message)


def test_validate_json_schema_missing_key():
    """Test JSON schema validation with a missing required key."""
    data = {"a": 1}
    schema = {"required": ["a", "b"]}
    with pytest.raises(PipelineError) as exc_info:
        validate_json_schema(data, schema)
    assert "Missing required key" in str(exc_info.value.message)


def test_validate_json_schema_type_mismatch():
    """Test JSON schema validation with a type mismatch."""
    data = {"a": "1"}
    schema = {"required": ["a"], "properties": {"a": "integer"}}
    with pytest.raises(PipelineError) as exc_info:
        validate_json_schema(data, schema)
    assert "Type mismatch" in str(exc_info.value.message)


def test_load_and_validate_yaml_success():
    """Test loading a valid YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"key": "value"}, f)
        path = Path(f.name)

    data = load_and_validate_yaml(path)
    assert data == {"key": "value"}
    path.unlink()


def test_load_and_validate_yaml_invalid_format():
    """Test loading a YAML file that is not a dictionary."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("just a string")
        path = Path(f.name)

    with pytest.raises(PipelineError) as exc_info:
        load_and_validate_yaml(path)
    assert "did not resolve to a dictionary" in str(exc_info.value.message)
    path.unlink()