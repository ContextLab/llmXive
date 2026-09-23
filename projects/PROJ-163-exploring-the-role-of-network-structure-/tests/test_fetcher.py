"""
Contract tests for API response schema parsing.

Validates that fetched backend properties conform to the defined JSON schema.
"""
import json
import os
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
import yaml

# Import the fetcher module to access its internal data structures if needed
# We assume the fetcher module is in the parent directory or code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.fetcher import fetch_backend_properties
from code.config import load_config

# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent / "specs" / "001-exploring-the-role-of-network-structure-" / "contracts" / "raw_calibration.schema.yaml"

@pytest.fixture
def schema():
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T009 is complete.")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def mock_backend_data():
    """
    Load the mock backend properties from the fixture created in T006b.
    This provides a deterministic, real-structure dataset for testing.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "mock_backend_properties.json"
    if not fixture_path.exists():
        pytest.fail(f"Mock fixture not found at {fixture_path}. Ensure T006b is complete.")
    
    with open(fixture_path, 'r') as f:
        return json.load(f)

def test_schema_is_valid_yaml_and_json_compatible(schema):
    """
    Verify that the loaded schema is a valid dictionary and follows JSON Schema draft-07.
    """
    assert isinstance(schema, dict), "Schema must be a dictionary."
    assert "$schema" in schema, "Schema must define the $schema keyword."
    assert "properties" in schema, "Schema must define top-level properties."
    
    # Validate that the schema itself is valid against Draft7Validator meta-schema
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(schema))
    assert len(errors) == 0, f"Schema itself is invalid: {[e.message for e in errors]}"

def test_contract_validation_with_mock_data(schema, mock_backend_data):
    """
    Contract test: Validate that the mock backend properties (representing real API structure)
    strictly conform to the defined schema.
    
    This ensures that if the API changes, the schema will catch it, or if the schema
    is too restrictive, it will be caught here.
    """
    try:
        validate(instance=mock_backend_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Mock data violates schema: {e.message}. "
                    f"Path: {list(e.path)}. "
                    f"Schema path: {list(e.schema_path)}. "
                    "Update schema or mock data to match real API structure.")

def test_contract_validation_missing_required_fields(schema):
    """
    Test that the schema correctly rejects data missing required fields.
    """
    invalid_data = {
        "device_id": "test_device",
        "timestamp": "2023-01-01T00:00:00Z"
        # Missing 'coupling_map' and 'properties'
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=schema)

def test_contract_validation_invalid_coupling_map_type(schema):
    """
    Test that the schema rejects a coupling_map that is not a list of lists of integers.
    """
    # Valid base data
    valid_base = {
        "device_id": "test_device",
        "timestamp": "2023-01-01T00:00:00Z",
        "coupling_map": [[0, 1], [1, 2]],
        "properties": {
            "qubits": [[{"name": "T1", "value": 100.0}]],
            "gates": []
        }
    }
    
    # Case 1: Coupling map is a list of integers, not lists
    invalid_data_1 = valid_base.copy()
    invalid_data_1["coupling_map"] = [0, 1, 2]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data_1, schema=schema)

def test_contract_validation_invalid_property_values(schema):
    """
    Test that the schema rejects property values that are not numbers where expected.
    """
    valid_base = {
        "device_id": "test_device",
        "timestamp": "2023-01-01T00:00:00Z",
        "coupling_map": [[0, 1]],
        "properties": {
            "qubits": [[{"name": "T1", "value": "invalid_string"}]],
            "gates": []
        }
    }
    
    with pytest.raises(ValidationError):
        validate(instance=valid_base, schema=schema)

@pytest.mark.integration
def test_live_api_response_conformance(schema):
    """
    Optional integration test: If IBMQ_TOKEN is available, fetch a real backend
    and validate it against the schema.
    """
    config = load_config()
    if not config.ibmq_token:
        pytest.skip("IBMQ_TOKEN not set. Skipping live API validation.")
    
    try:
        # Fetch properties for a known device (e.g., ibmq_quito or ibmq_manila)
        # We use a small subset to avoid rate limits in CI if possible, 
        # but this test requires a real fetch.
        backend_name = "ibmq_quito"
        
        # Note: This relies on the implementation in fetcher.py
        # If fetch_backend_properties returns a dict directly
        result = fetch_backend_properties(backend_name)
        
        if result is None:
            pytest.skip(f"Could not fetch properties for {backend_name}. Skipping.")
        
        validate(instance=result, schema=schema)
        
    except ValidationError as e:
        pytest.fail(f"Real API response for {backend_name} violates schema: {e.message}")
    except Exception as e:
        # Network errors or API issues are expected in some CI environments
        pytest.skip(f"Live API fetch failed: {str(e)}. Skipping validation.")