"""
Unit tests for schema validation logic.

Validates that the schema definitions in `contracts/*.schema.yaml` are:
1. Valid YAML files.
2. Conform to the expected structure (containing 'fields' and 'description').
3. Match the definitions expected by the code generators (e.g., MessageEnvelope, MetricRecord).
"""

import os
import yaml
import json
import pytest
from pathlib import Path

# Define the project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Expected schema files based on T004 and T005
EXPECTED_SCHEMAS = {
    "dataset.schema.yaml": {
        "name": "MessageEnvelope",
        "required_fields": [
            "sender_id",
            "receiver_id",
            "timestamp",
            "signature",
            "payload_size",
            "checkpoint_ref"
        ]
    },
    "metrics.schema.yaml": {
        "name": "MetricRecord",
        "required_fields": [
            "seed",
            "protocol",
            "episode_length",
            "msg_count",
            "bytes_sent",
            "recovery_success",
            "recovery_latency",
            "task_success"
        ]
    }
}


def load_schema(filename: str) -> dict:
    """Load a schema file from the contracts directory."""
    filepath = CONTRACTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Schema file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        raise ValueError(f"Schema {filename} must be a YAML dictionary")
    
    return data


class TestSchemaFileExistence:
    """Test that all expected schema files exist."""

    @pytest.mark.parametrize("filename", EXPECTED_SCHEMAS.keys())
    def test_schema_file_exists(self, filename):
        filepath = CONTRACTS_DIR / filename
        assert filepath.exists(), f"Expected schema file {filename} to exist in {CONTRACTS_DIR}"


class TestSchemaStructure:
    """Test that schema files have valid YAML structure and required top-level keys."""

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_is_valid_yaml(self, filename, expected):
        """Verify the file is valid YAML and is a dictionary."""
        try:
            data = load_schema(filename)
            assert isinstance(data, dict), f"Schema {filename} must be a dictionary"
        except yaml.YAMLError as e:
            pytest.fail(f"Schema {filename} is not valid YAML: {e}")
        except FileNotFoundError:
            # This is covered by existence tests, but safe to re-raise here
            raise

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_has_name_field(self, filename, expected):
        """Verify schema has a 'name' field matching the expected entity."""
        data = load_schema(filename)
        assert "name" in data, f"Schema {filename} missing 'name' field"
        assert data["name"] == expected["name"], f"Schema {filename} name mismatch: expected {expected['name']}, got {data['name']}"

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_has_fields_list(self, filename, expected):
        """Verify schema has a 'fields' list."""
        data = load_schema(filename)
        assert "fields" in data, f"Schema {filename} missing 'fields' key"
        assert isinstance(data["fields"], list), f"Schema {filename} 'fields' must be a list"


class TestSchemaFieldContent:
    """Test that schema files contain the specific required fields defined in the spec."""

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_contains_required_fields(self, filename, expected):
        """Verify all required fields are present in the schema's field list."""
        data = load_schema(filename)
        schema_fields = [f.get("name") if isinstance(f, dict) else f for f in data["fields"]]
        
        missing_fields = set(expected["required_fields"]) - set(schema_fields)
        assert not missing_fields, f"Schema {filename} is missing required fields: {missing_fields}"

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_field_format(self, filename, expected):
        """Verify fields are dictionaries with 'name' and 'type' (or similar structure)."""
        data = load_schema(filename)
        for field in data["fields"]:
            if isinstance(field, dict):
                assert "name" in field, f"Field in {filename} must have a 'name' key"
                assert "type" in field, f"Field '{field['name']}' in {filename} must have a 'type' key"
            else:
                # If fields are just strings, ensure they match the required list
                assert field in expected["required_fields"], f"Unexpected field format in {filename}: {field}"


class TestSchemaJSONCompatibility:
    """Test that schemas can be converted to JSON (for downstream tooling)."""

    @pytest.mark.parametrize("filename, expected", EXPECTED_SCHEMAS.items())
    def test_schema_serializes_to_json(self, filename, expected):
        """Verify the schema structure is JSON-serializable."""
        data = load_schema(filename)
        try:
            json_str = json.dumps(data)
            assert len(json_str) > 0
            # Verify round-trip
            restored = json.loads(json_str)
            assert restored == data
        except TypeError as e:
            pytest.fail(f"Schema {filename} is not JSON serializable: {e}")


def test_contract_directory_not_empty():
    """Sanity check that the contracts directory is not empty."""
    assert CONTRACTS_DIR.exists(), "Contracts directory does not exist"
    files = list(CONTRACTS_DIR.glob("*.yaml")) + list(CONTRACTS_DIR.glob("*.yml"))
    assert len(files) > 0, "No schema files found in contracts directory"