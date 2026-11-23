"""
Unit tests for the data_version.json schema definition.

This ensures that the schema file exists and defines the required fields:
source_url, checksum_sha256, and timestamp.
"""
import json
import os
from pathlib import Path
import pytest
from jsonschema import validate, ValidationError

# Path relative to the project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "data" / "schemas" / "data_version.schema.json"


class TestDataVersionSchema:
    """Tests for the data_version.json schema structure."""

    def test_schema_file_exists(self):
        """Verify that the schema file exists at the expected path."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self):
        """Verify that the schema file contains valid JSON."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            try:
                schema = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Schema file is not valid JSON: {e}")
            assert isinstance(schema, dict), "Schema root must be an object"

    def test_schema_contains_required_fields(self):
        """Verify the schema defines the three required fields."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        required_fields = schema.get("required", [])
        assert "source_url" in required_fields, "source_url must be a required field"
        assert "checksum_sha256" in required_fields, "checksum_sha256 must be a required field"
        assert "timestamp" in required_fields, "timestamp must be a required field"

    def test_schema_validates_correct_instance(self):
        """Verify that a valid data version object passes schema validation."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        valid_instance = {
            "source_url": "https://example.com/data.csv",
            "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "timestamp": "2023-10-27T10:00:00Z"
        }

        try:
            validate(instance=valid_instance, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid instance failed schema validation: {e.message}")

    def test_schema_rejects_missing_field(self):
        """Verify that an instance missing a required field fails validation."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        invalid_instance = {
            "source_url": "https://example.com/data.csv",
            "timestamp": "2023-10-27T10:00:00Z"
            # Missing checksum_sha256
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_instance, schema=schema)

    def test_checksum_format_validation(self):
        """Verify that the checksum field enforces the 64-char hex pattern."""
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

        invalid_checksum_instance = {
            "source_url": "https://example.com/data.csv",
            "checksum_sha256": "short_hash",
            "timestamp": "2023-10-27T10:00:00Z"
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_checksum_instance, schema=schema)