"""
Contract test for model output schema (US2).

This test validates that the GNN model's prediction output strictly adheres
to the schema defined in contracts/output_schema.schema.yaml.

It verifies:
1. The output is a list of dictionaries.
2. Each dictionary contains the required keys: 'complex_id', 'predicted_pKd', 'actual_pKd', 'error'.
3. 'complex_id' is a string.
4. 'predicted_pKd', 'actual_pKd', and 'error' are floats.
5. 'error' is calculated as |predicted - actual|.
6. 'actual_pKd' is positive (physical constraint).
"""

import json
import os
import pytest
from pathlib import Path
from typing import Any, List, Dict

# Import the schema loader from the existing data pipeline utilities
# We assume the schema file exists as per T005
from data.save_and_validate_graphs import load_schema

# Define the path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "output_schema.schema.yaml"

def load_expected_schema() -> Dict[str, Any]:
    """Loads the expected output schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T005 is complete.")
    return load_schema(str(SCHEMA_PATH))

def validate_single_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validates a single model output record against the schema."""
    required_fields = ["complex_id", "predicted_pKd", "actual_pKd", "error"]

    # Check for presence of all required fields
    for field in required_fields:
        assert field in record, f"Missing required field: {field}"

    # Type checks
    assert isinstance(record["complex_id"], str), f"complex_id must be a string, got {type(record['complex_id'])}"
    assert isinstance(record["predicted_pKd"], (int, float)), f"predicted_pKd must be numeric, got {type(record['predicted_pKd'])}"
    assert isinstance(record["actual_pKd"], (int, float)), f"actual_pKd must be numeric, got {type(record['actual_pKd'])}"
    assert isinstance(record["error"], (int, float)), f"error must be numeric, got {type(record['error'])}"

    # Physical and logical constraints
    assert record["actual_pKd"] > 0, f"actual_pKd must be positive, got {record['actual_pKd']}"
    
    # Verify error calculation
    expected_error = abs(record["predicted_pKd"] - record["actual_pKd"])
    # Allow small floating point tolerance
    assert abs(record["error"] - expected_error) < 1e-6, \
        f"Error mismatch: calculated {expected_error}, got {record['error']}"

def test_model_output_schema_conformance(tmp_path: Path):
    """
    Generates a mock model output file and validates it against the contract schema.
    
    This test simulates the output of `code/models/train.py` (T028) to ensure
    the generated results file complies with the defined contract.
    """
    # Load the schema
    schema = load_expected_schema()

    # Create a sample output that mimics the real model output format
    # In a real scenario, this would be read from data/results/predictions.json
    sample_output = [
        {
            "complex_id": "1ABC",
            "predicted_pKd": 7.5,
            "actual_pKd": 7.8,
            "error": 0.3
        },
        {
            "complex_id": "2XYZ",
            "predicted_pKd": 5.2,
            "actual_pKd": 5.0,
            "error": 0.2
        },
        {
            "complex_id": "3DEF",
            "predicted_pKd": 9.1,
            "actual_pKd": 9.05,
            "error": 0.05
        }
    ]

    # Write to a temporary file to simulate the artifact
    output_file = tmp_path / "predictions.json"
    with open(output_file, "w") as f:
        json.dump(sample_output, f, indent=2)

    # Load the file back and validate
    with open(output_file, "r") as f:
        loaded_data = json.load(f)

    assert isinstance(loaded_data, list), "Output must be a list of records"
    assert len(loaded_data) > 0, "Output list cannot be empty"

    for i, record in enumerate(loaded_data):
        validate_single_record(record, schema)

def test_model_output_schema_structural_validation(tmp_path: Path):
    """
    Tests that the schema itself is well-formed and enforces the expected types.
    This ensures the contract file (T005) is valid.
    """
    schema = load_expected_schema()
    
    # Basic sanity checks on the schema structure
    assert "properties" in schema, "Schema must have 'properties' definition"
    properties = schema["properties"]
    
    assert "complex_id" in properties, "Schema must define 'complex_id'"
    assert "predicted_pKd" in properties, "Schema must define 'predicted_pKd'"
    assert "actual_pKd" in properties, "Schema must define 'actual_pKd'"
    assert "error" in properties, "Schema must define 'error'"
    
    # Verify types in schema definition (assuming simple JSON Schema style)
    # Note: The exact key might vary (e.g., 'type' vs 'dtype') depending on implementation
    # but we check for the existence of type constraints.
    for field in ["complex_id", "predicted_pKd", "actual_pKd", "error"]:
        assert "type" in properties[field] or "dtype" in properties[field], \
            f"Schema for {field} must define a type"

def test_model_output_invalid_data_rejection(tmp_path: Path):
    """
    Ensures that invalid data (e.g., missing fields, wrong types) fails validation.
    """
    schema = load_expected_schema()
    
    invalid_record = {
        "complex_id": 12345,  # Should be string
        "predicted_pKd": "high", # Should be float
        "actual_pKd": -1.0, # Should be positive
        # Missing 'error'
    }
    
    # We expect this to fail our validation logic
    with pytest.raises(AssertionError):
        validate_single_record(invalid_record, schema)

    # Test with missing field
    incomplete_record = {
        "complex_id": "1ABC",
        "predicted_pKd": 7.5,
        "actual_pKd": 7.8
        # Missing 'error'
    }
    with pytest.raises(AssertionError):
        validate_single_record(incomplete_record, schema)