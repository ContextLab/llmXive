"""
Contract tests for PowerEstimate JSON schema validation.

This module validates that the output of the power estimation pipeline
conforms to the schema defined in contracts/power_estimate.schema.yaml.

Expected behavior:
- Tests should FAIL initially if the schema file is missing or the pipeline
  does not yet produce valid output.
- Tests should PASS once the pipeline generates valid JSON matching the schema.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils import safe_json_load

SCHEMA_PATH = project_root / "contracts" / "power_estimate.schema.yaml"
RESULTS_PATH = project_root / "data" / "results" / "baseline.json"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found at {SCHEMA_PATH}. "
            "Ensure T007 (Define contracts) is completed."
        )
    
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def load_baseline_results() -> Dict[str, Any]:
    """Load the baseline results JSON file."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Results file not found at {RESULTS_PATH}. "
            "Ensure the pipeline (T014) has been run to generate baseline.json."
        )
    
    return safe_json_load(RESULTS_PATH)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against the JSON schema.
    
    Note: This is a simple validation implementation. For production use,
    consider using the 'jsonschema' library:
    `import jsonschema; jsonschema.validate(data, schema)`
    
    Here we implement basic checks for the required keys and types
    as defined in the schema.
    """
    # Check required properties
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise AssertionError(f"Missing required key: {key}")
    
    # Check property types
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise AssertionError(f"Field '{key}' must be a number, got {type(value)}")
            elif expected_type == "string":
                if not isinstance(value, str):
                    raise AssertionError(f"Field '{key}' must be a string, got {type(value)}")
            elif expected_type == "array":
                if not isinstance(value, list):
                    raise AssertionError(f"Field '{key}' must be an array, got {type(value)}")
            # Add more type checks as needed based on schema complexity
    
    return True

class TestPowerEstimateSchema:
    """Contract tests for the PowerEstimate schema."""

    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "type" in schema, "Schema must have a 'type' field"
        assert schema["type"] == "object", "Schema type must be 'object'"

    def test_baseline_results_exist(self):
        """Test that the baseline results file exists."""
        # This test will FAIL initially if the pipeline hasn't run yet
        assert RESULTS_PATH.exists(), f"Baseline results file missing: {RESULTS_PATH}"

    def test_baseline_results_loadable(self):
        """Test that the baseline results file is valid JSON."""
        data = load_baseline_results()
        assert isinstance(data, list), "Baseline results must be a list of objects"
        assert len(data) > 0, "Baseline results list is empty"

    def test_baseline_results_conform_to_schema(self):
        """
        Test that each record in baseline_results conforms to the PowerEstimate schema.
        
        This is the primary contract test. It will FAIL if:
        1. The schema is missing required keys (theoretical_power, empirical_power, absolute_error).
        2. The pipeline output does not match the schema types.
        """
        schema = load_schema()
        data = load_baseline_results()

        for i, record in enumerate(data):
            try:
                validate_against_schema(record, schema)
            except AssertionError as e:
                pytest.fail(f"Record {i} failed schema validation: {e}")

    def test_required_fields_present(self):
        """
        Explicit check for the three required fields defined in the task:
        theoretical_power, empirical_power, absolute_error.
        """
        data = load_baseline_results()
        required_keys = {"theoretical_power", "empirical_power", "absolute_error"}

        for i, record in enumerate(data):
            missing = required_keys - set(record.keys())
            if missing:
                pytest.fail(f"Record {i} missing required fields: {missing}")