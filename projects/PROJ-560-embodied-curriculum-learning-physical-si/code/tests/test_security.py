"""
Tests for security hardening in data loading.

These tests verify that:
1. Arbitrary code execution is prevented in YAML loading.
2. Path traversal attacks are blocked.
3. Invalid file types are rejected.
4. Schema validation works correctly.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import yaml

from src.security import (
    sanitize_file_path,
    load_safe_csv,
    load_safe_json,
    load_safe_yaml,
    validate_schema,
    load_dataset_secure,
    SafeYamlLoader
)

class TestSecurityPathSanitization:
    """Tests for path traversal prevention."""

    def test_valid_path(self, tmp_path):
        """Valid path within root should succeed."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("a,b\n1,2")
        
        result = sanitize_file_path(str(test_file), allowed_root=tmp_path)
        assert result == test_file.resolve()

    def test_path_traversal_blocked(self, tmp_path):
        """Path traversal (..) should be blocked."""
        # Create a file outside tmp_path
        outside_file = tmp_path.parent / "secret.csv"
        outside_file.write_text("secret")
        
        # Try to access it via traversal
        malicious_path = f"{tmp_path}/subdir/../../secret.csv"
        
        with pytest.raises(ValueError, match="outside the allowed directory"):
            sanitize_file_path(malicious_path, allowed_root=tmp_path)

    def test_null_byte_injection(self, tmp_path):
        """Null bytes in path should be rejected."""
        malicious_path = f"{tmp_path}/data.csv\x00.jpg"
        
        with pytest.raises(ValueError, match="null bytes"):
            sanitize_file_path(malicious_path, allowed_root=tmp_path)

    def test_empty_path(self):
        """Empty path should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sanitize_file_path("")

class TestSecureYamlLoading:
    """Tests for preventing ACE in YAML loading."""

    def test_safe_yaml_load(self, tmp_path):
        """Standard safe YAML should load correctly."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("key: value\nlist:\n  - 1\n  - 2")
        
        data = load_safe_yaml(str(yaml_file), allowed_root=tmp_path)
        assert data["key"] == "value"
        assert data["list"] == [1, 2]

    def test_exploit_yaml_blocked(self, tmp_path):
        """
        Attempt to load YAML with Python object instantiation should fail.
        
        This is the core security test. A malicious YAML file like:
        !!python/object/apply:os.system ['echo pwned']
        must not execute code.
        """
        yaml_file = tmp_path / "malicious.yaml"
        # This is a standard exploit payload for unsafe yaml.load
        yaml_content = """
        !!python/object/apply:os.system
        args: ['echo EXPLOIT_SUCCESS']
        """
        yaml_file.write_text(yaml_content)
        
        # We expect this to raise an error or return None, but NOT execute code.
        # SafeLoader should reject the !!python/object tag.
        with pytest.raises(yaml.YAMLError):
            load_safe_yaml(str(yaml_file), allowed_root=tmp_path)

    def test_custom_safe_loader_rejects_python_tags(self):
        """Verify SafeYamlLoader does not accept python/object tags."""
        yaml_content = "!!python/object/apply:os.system ['echo test']"
        
        # If we try to load this with SafeYamlLoader, it should fail
        with pytest.raises(yaml.YAMLError):
            yaml.load(yaml_content, Loader=SafeYamlLoader)

class TestSecureJsonLoading:
    """Tests for secure JSON loading."""

    def test_valid_json(self, tmp_path):
        """Valid JSON should load."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"name": "test", "value": 123}')
        
        data = load_safe_json(str(json_file), allowed_root=tmp_path)
        assert data["name"] == "test"

    def test_invalid_json(self, tmp_path):
        """Invalid JSON should raise error."""
        json_file = tmp_path / "bad.json"
        json_file.write_text('{invalid json}')
        
        with pytest.raises(json.JSONDecodeError):
            load_safe_json(str(json_file), allowed_root=tmp_path)

    def test_wrong_extension(self, tmp_path):
        """Loading JSON with wrong extension should fail."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text('{"name": "test"}') # Content is JSON, ext is CSV
        
        with pytest.raises(ValueError, match="Invalid file extension"):
            load_safe_json(str(csv_file), allowed_root=tmp_path)

class TestSecureCsvLoading:
    """Tests for secure CSV loading."""

    def test_valid_csv(self, tmp_path):
        """Valid CSV should load."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n3,4")
        
        data = load_safe_csv(str(csv_file), allowed_root=tmp_path)
        assert len(data) == 2
        assert data[0]["a"] == "1"

    def test_missing_file(self, tmp_path):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_safe_csv(str(tmp_path / "missing.csv"), allowed_root=tmp_path)

class TestSchemaValidation:
    """Tests for schema validation."""

    def test_valid_schema(self):
        """Data with required columns should pass."""
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert validate_schema(data, {"a", "b"}) is True

    def test_missing_columns(self):
        """Data missing required columns should raise ValueError."""
        data = [{"a": 1, "c": 2}]
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(data, {"a", "b"})

    def test_empty_data(self):
        """Empty data list should pass validation (with warning)."""
        assert validate_schema([], {"a", "b"}) is True

class TestUnifiedSecureLoader:
    """Tests for the unified load_dataset_secure function."""

    def test_csv_dispatch(self, tmp_path):
        """Correctly dispatches to CSV loader."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1,col2\n1,2")
        
        data = load_dataset_secure(str(csv_file), "csv", allowed_root=tmp_path)
        assert len(data) == 1

    def test_json_dispatch(self, tmp_path):
        """Correctly dispatches to JSON loader."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"col1": 1}')
        
        data = load_dataset_secure(str(json_file), "json", allowed_root=tmp_path)
        assert data["col1"] == 1

    def test_yaml_dispatch(self, tmp_path):
        """Correctly dispatch to YAML loader."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("col1: 1")
        
        data = load_dataset_secure(str(yaml_file), "yaml", allowed_root=tmp_path)
        assert data["col1"] == 1

    def test_unsupported_type(self, tmp_path):
        """Unsupported file type raises ValueError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("data")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_dataset_secure(str(txt_file), "txt", allowed_root=tmp_path)

    def test_schema_validation_integration(self, tmp_path):
        """Validates schema if required_columns provided."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2")
        
        # Should pass
        data = load_dataset_secure(str(csv_file), "csv", required_columns={"a", "b"}, allowed_root=tmp_path)
        assert len(data) == 1
        
        # Should fail
        with pytest.raises(ValueError, match="Missing required columns"):
            load_dataset_secure(str(csv_file), "csv", required_columns={"a", "c"}, allowed_root=tmp_path)