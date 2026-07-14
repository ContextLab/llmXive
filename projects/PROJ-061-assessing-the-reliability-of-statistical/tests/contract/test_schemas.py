"""
Contract tests for PowerEstimate JSON schema validation.

This module validates that power estimate results conform to the 
contracts/power_estimate.schema.yaml specification.

Expected to FAIL initially until the schema and implementation are ready.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict
import yaml

# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "power_estimate.schema.yaml"
# Path to a sample results file (may not exist yet)
SAMPLE_RESULTS_PATH = Path(__file__).parent.parent.parent / "data" / "results" / "baseline.json"


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    return schema


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against the schema manually (since jsonschema might not be installed).
    
    Returns True if valid, raises AssertionError if invalid.
    """
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            raise AssertionError(f"Missing required field: {field}")
    
    # Check types for known fields
    properties = schema.get('properties', {})
    
    if 'theoretical_power' in data:
        if not isinstance(data['theoretical_power'], (int, float)):
            raise AssertionError("theoretical_power must be a number")
    
    if 'empirical_power' in data:
        if not isinstance(data['empirical_power'], (int, float)):
            raise AssertionError("empirical_power must be a number")
    
    if 'absolute_error' in data:
        if not isinstance(data['absolute_error'], (int, float)):
            raise AssertionError("absolute_error must be a number")
    
    return True


class TestPowerEstimateSchema:
    """Contract tests for PowerEstimate schema validation."""

    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        assert SCHEMA_PATH.exists(), "Schema file must exist for validation"

    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert 'properties' in schema, "Schema must define properties"
        assert 'required' in schema, "Schema must define required fields"

    def test_validate_valid_power_estimate(self):
        """Test validation of a correctly formatted power estimate."""
        schema = load_schema()
        
        valid_estimate = {
            "theoretical_power": 0.80,
            "empirical_power": 0.78,
            "absolute_error": 0.02
        }
        
        # This should not raise an exception
        validate_against_schema(valid_estimate, schema)

    def test_validate_missing_required_field(self):
        """Test that missing required fields cause validation failure."""
        schema = load_schema()
        
        invalid_estimate = {
            "theoretical_power": 0.80
            # Missing empirical_power and absolute_error
        }
        
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(invalid_estimate, schema)
        
        assert "Missing required field" in str(exc_info.value)

    def test_validate_wrong_type(self):
        """Test that wrong types cause validation failure."""
        schema = load_schema()
        
        invalid_estimate = {
            "theoretical_power": "0.80",  # Should be number, not string
            "empirical_power": 0.78,
            "absolute_error": 0.02
        }
        
        with pytest.raises(AssertionError) as exc_info:
            validate_against_schema(invalid_estimate, schema)
        
        assert "must be a number" in str(exc_info.value)

    def test_validate_baseline_results_file(self):
        """Test validation of the actual baseline results file if it exists."""
        if not SAMPLE_RESULTS_PATH.exists():
            pytest.skip("Baseline results file not yet generated")
        
        with open(SAMPLE_RESULTS_PATH, 'r') as f:
            data = json.load(f)
        
        schema = load_schema()
        
        # If baseline.json is a list of estimates, validate each
        if isinstance(data, list):
            for estimate in data:
                validate_against_schema(estimate, schema)
        else:
            validate_against_schema(data, schema)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
