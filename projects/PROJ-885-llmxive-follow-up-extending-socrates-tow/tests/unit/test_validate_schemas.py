"""
Unit tests for scripts/validate_schemas.py logic.

These tests verify the schema validation logic without requiring
the full pipeline to run.
"""

import json
import pytest
from pathlib import Path
from typing import List

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.validate_schemas import validate_dict_schema, validate_schema, load_json_file

class TestValidateDictSchema:
    """Tests for the validate_dict_schema function."""

    def test_empty_list(self):
        """Empty list should pass validation."""
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id"],
                "key_types": {"id": str}
            }
        }
        errors = validate_dict_schema([], schema)
        assert len(errors) == 0

    def test_missing_required_key(self):
        """Missing required key should produce an error."""
        data = [{"id": 1, "name": "test"}]
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id", "name", "value"],
                "key_types": {"id": int, "name": str, "value": str}
            }
        }
        errors = validate_dict_schema(data, schema)
        assert len(errors) == 1
        assert "Missing required key 'value'" in errors[0]

    def test_wrong_type(self):
        """Wrong type for a key should produce an error."""
        data = [{"id": "not_int", "name": "test", "value": "val"}]
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id", "name", "value"],
                "key_types": {"id": int, "name": str, "value": str}
            }
        }
        errors = validate_dict_schema(data, schema)
        assert len(errors) == 1
        assert "has type str, expected int" in errors[0]

    def test_valid_data(self):
        """Valid data should produce no errors."""
        data = [
            {"id": 1, "name": "test", "value": "val"},
            {"id": 2, "name": "test2", "value": "val2"}
        ]
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id", "name", "value"],
                "key_types": {"id": int, "name": str, "value": str}
            }
        }
        errors = validate_dict_schema(data, schema)
        assert len(errors) == 0

    def test_non_list_input(self):
        """Non-list input should produce an error."""
        data = {"id": 1}
        schema = {
            "type": "list",
            "item_schema": {"type": "dict", "required_keys": ["id"]}
        }
        errors = validate_dict_schema(data, schema)
        assert len(errors) == 1
        assert "Expected data to be a list" in errors[0]

class TestValidateSchema:
    """Tests for the validate_schema function."""

    def test_file_not_found(self, tmp_path):
        """Missing file should result in valid=False and error message."""
        fake_path = tmp_path / "nonexistent.json"
        schema = {"type": "list", "item_schema": {}}
        
        result = validate_schema(fake_path, schema, "test")
        
        assert result["schema_valid"] is False
        assert len(result["errors"]) == 1
        assert "Failed to load file" in result["errors"][0]

    def test_valid_file(self, tmp_path):
        """Valid JSON file should pass validation."""
        data = [{"id": 1, "name": "test"}]
        file_path = tmp_path / "valid.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id", "name"],
                "key_types": {"id": int, "name": str}
            }
        }
        
        result = validate_schema(file_path, schema, "test")
        
        assert result["schema_valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_file(self, tmp_path):
        """Invalid JSON file should fail validation."""
        data = [{"id": "not_int", "name": "test"}]
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        schema = {
            "type": "list",
            "item_schema": {
                "type": "dict",
                "required_keys": ["id", "name"],
                "key_types": {"id": int, "name": str}
            }
        }
        
        result = validate_schema(file_path, schema, "test")
        
        assert result["schema_valid"] is False
        assert len(result["errors"]) > 0

class TestLoadJsonFile:
    """Tests for the load_json_file function."""

    def test_load_valid_json(self, tmp_path):
        """Should load valid JSON correctly."""
        data = {"key": "value"}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_json_file(file_path)
        assert result == data

    def test_load_invalid_json(self, tmp_path):
        """Should return None for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("not valid json {{{")
        
        result = load_json_file(file_path)
        assert result is None

    def test_load_missing_file(self, tmp_path):
        """Should return None for missing file."""
        file_path = tmp_path / "missing.json"
        result = load_json_file(file_path)
        assert result is None