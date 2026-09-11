"""
Contract tests for API response schema parsing in fetcher.py.
Validates raw calibration data against the defined JSON schema.
"""
import os
import json
import pytest
from jsonschema import validate, ValidationError, Draft7Validator
from pathlib import Path

# Import the fetcher module to access any helper functions if needed,
# though the primary focus here is on schema validation.
# Note: We assume fetcher.py is in the code/ directory relative to the project root.
# If running from tests/, we might need to adjust the import path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetcher import fetch_backend_properties

# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent / "specs/001-explore-network-structure-superconducting-qubit-coupling" / "contracts" / "raw_calibration.schema.yaml"

import yaml

@pytest.fixture
def schema():
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_schema_loads_correctly(schema):
    """Ensure the schema itself is valid and loads without error."""
    assert schema is not None
    assert "type" in schema
    assert schema["type"] == "object"
    # Verify required fields exist
    assert "required" in schema
    assert "backend_name" in schema["required"]

def test_validate_sample_structure(schema):
    """
    Validate a manually constructed sample that mimics the expected structure
    to ensure the schema validation logic works as intended.
    """
    sample_data = {
        "backend_name": "test_backend",
        "backend_version": "1.0.0",
        "last_update_date": "2023-10-27T10:00:00Z",
        "qubits": [
            [
                {"name": "T1", "value": 100.0},
                {"name": "T2", "value": 50.0}
            ]
        ],
        "gates": [
            {
                "gate": "cx",
                "qubits": [0, 1],
                "parameters": [],
                "gate_error": 0.01
            }
        ],
        "general": [
            {"name": "coupling_map", "value": [[0, 1]]},
            {"name": "basis_gates", "value": ["u1", "u2", "u3", "cx"]}
        ]
    }

    try:
        validate(instance=sample_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Sample data failed schema validation: {e.message}")

def test_validate_invalid_missing_field(schema):
    """Ensure validation fails when a required field is missing."""
    invalid_data = {
        "backend_name": "test_backend",
        # Missing backend_version, last_update_date, qubits, etc.
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_validate_invalid_type(schema):
    """Ensure validation fails when a field has an incorrect type."""
    invalid_data = {
        "backend_name": 12345,  # Should be string
        "backend_version": "1.0.0",
        "last_update_date": "2023-10-27T10:00:00Z",
        "qubits": [],
        "gates": [],
        "general": []
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

# Note: We do not run fetch_backend_properties here in a full integration test
# because that is covered by T011 (Integration test for live API fetch).
# This task (T010) is specifically for the contract test (schema validation).
# However, if we want to test the schema against a real fetched object (if available),
# we could do so, but it requires network access and a valid token.
# Given the constraints, we rely on the mock/sample validation above.
# If a real fetch is needed for the schema test, it would be:
# def test_validate_real_fetch(schema):
#     # Requires environment setup for IBM Quantum
#     # This is more of an integration test, so we keep it minimal here.
#     pass