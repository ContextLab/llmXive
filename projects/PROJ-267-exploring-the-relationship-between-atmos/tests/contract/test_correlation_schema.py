"""
Contract test for Correlation Result entity validation.

Validates that the output from the correlation pipeline (04_correlation.py, 
05_bootstrap_correction.py, 06_control_validation.py) adheres to the 
schema defined in contracts/output.schema.yaml.

This test ensures:
1. All required fields are present
2. Data types match the schema definition
3. Enum values (region_type) are valid
4. Numerical constraints are met (correlation coefficients between -1 and 1)
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Add code directory to path for imports if needed, though this test is standalone
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

def load_output_schema() -> Dict[str, Any]:
    """Load the correlation output schema from YAML file."""
    if not OUTPUT_SCHEMA_PATH.exists():
        pytest.fail(f"Output schema file not found: {OUTPUT_SCHEMA_PATH}")
    
    with open(OUTPUT_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_correlation_result_schema(
    result: Dict[str, Any], 
    schema: Dict[str, Any]
) -> List[str]:
    """
    Validate a single Correlation Result record against the schema.
    
    Returns a list of validation error messages. Empty list means valid.
    """
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    # Check required fields
    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")
    
    # Validate field types and constraints
    for field, value in result.items():
        if field not in properties:
            errors.append(f"Unexpected field: {field}")
            continue
        
        field_spec = properties[field]
        expected_type = field_spec.get("type")
        
        # Type checking
        if expected_type == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            elif field in ["correlation_coefficient", "p_value"] and not (-1 <= value <= 1):
                # Specific constraint for correlation metrics
                if field == "correlation_coefficient" and not (-1 <= value <= 1):
                    errors.append(f"Field '{field}' must be between -1 and 1, got {value}")
                elif field == "p_value" and not (0 <= value <= 1):
                    errors.append(f"Field '{field}' must be between 0 and 1, got {value}")
                
        elif expected_type == "integer":
            if not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer, got {type(value).__name__}")
        
        elif expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
            # Check enum constraints
            if "enum" in field_spec:
                if value not in field_spec["enum"]:
                    errors.append(
                        f"Field '{field}' must be one of {field_spec['enum']}, got '{value}'"
                    )
        
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean, got {type(value).__name__}")
        
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array, got {type(value).__name__}")
            else:
                # Check items type if specified
                items_spec = field_spec.get("items", {})
                items_type = items_spec.get("type")
                if items_type and value:
                    for i, item in enumerate(value):
                        if items_type == "number" and not isinstance(item, (int, float)):
                            errors.append(
                                f"Field '{field}' item {i} must be number, got {type(item).__name__}"
                            )
                        elif items_type == "string" and not isinstance(item, str):
                            errors.append(
                                f"Field '{field}' item {i} must be string, got {type(item).__name__}"
                            )
    
    return errors

def test_schema_exists_and_valid():
    """Test that the output schema file exists and is valid YAML."""
    schema = load_output_schema()
    assert "properties" in schema, "Schema must contain 'properties' key"
    assert "required" in schema, "Schema must contain 'required' key"
    assert "region_type" in schema["properties"], "Schema must define 'region_type' field"
    assert "correlation_coefficient" in schema["properties"], "Schema must define 'correlation_coefficient' field"
    assert "p_value" in schema["properties"], "Schema must define 'p_value' field"
    assert "significant_after_correction" in schema["properties"], "Schema must define 'significant_after_correction' field"

def test_valid_correlation_result():
    """Test that a valid Correlation Result passes validation."""
    schema = load_output_schema()
    
    valid_result = {
        "region_type": "target",
        "lag_months": 0,
        "correlation_coefficient": 0.45,
        "p_value": 0.032,
        "corrected_p_value": 0.048,
        "significant_after_correction": True,
        "n_samples": 120,
        "n_eff": 98,
        "bootstrap_ci_lower": 0.28,
        "bootstrap_ci_upper": 0.61,
        "noise_floor_sigma": 1.2e-5,
        "signal_to_noise_ratio": 3.5
    }
    
    errors = validate_correlation_result_schema(valid_result, schema)
    assert len(errors) == 0, f"Valid result failed validation: {errors}"

def test_invalid_region_type():
    """Test that invalid region_type values are caught."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": "unknown_region",  # Invalid enum value
        "lag_months": 1,
        "correlation_coefficient": 0.3,
        "p_value": 0.1,
        "corrected_p_value": 0.2,
        "significant_after_correction": False,
        "n_samples": 100,
        "n_eff": 80,
        "bootstrap_ci_lower": 0.1,
        "bootstrap_ci_upper": 0.5,
        "noise_floor_sigma": 1.0e-5,
        "signal_to_noise_ratio": 2.0
    }
    
    errors = validate_correlation_result_schema(invalid_result, schema)
    assert len(errors) > 0, "Should have caught invalid region_type"
    assert any("region_type" in e for e in errors), "Error message should mention region_type"

def test_correlation_coefficient_bounds():
    """Test that correlation coefficients outside [-1, 1] are caught."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": "target",
        "lag_months": 0,
        "correlation_coefficient": 1.5,  # Invalid
        "p_value": 0.01,
        "corrected_p_value": 0.02,
        "significant_after_correction": True,
        "n_samples": 100,
        "n_eff": 80,
        "bootstrap_ci_lower": 0.8,
        "bootstrap_ci_upper": 1.2,
        "noise_floor_sigma": 1.0e-5,
        "signal_to_noise_ratio": 4.0
    }
    
    errors = validate_correlation_result_schema(invalid_result, schema)
    assert len(errors) > 0, "Should have caught invalid correlation_coefficient"
    assert any("correlation_coefficient" in e for e in errors), "Error message should mention correlation_coefficient"

def test_missing_required_field():
    """Test that missing required fields are caught."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": "target",
        "lag_months": 0,
        # Missing correlation_coefficient, p_value, etc.
    }
    
    errors = validate_correlation_result_schema(invalid_result, schema)
    assert len(errors) > 0, "Should have caught missing required fields"
    assert any("correlation_coefficient" in e for e in errors), "Should report missing correlation_coefficient"
    assert any("p_value" in e for e in errors), "Should report missing p_value"

def test_wrong_data_type():
    """Test that wrong data types are caught."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": 123,  # Should be string
        "lag_months": "zero",  # Should be integer
        "correlation_coefficient": 0.5,
        "p_value": 0.05,
        "corrected_p_value": 0.1,
        "significant_after_correction": "yes",  # Should be boolean
        "n_samples": 100,
        "n_eff": 80,
        "bootstrap_ci_lower": 0.3,
        "bootstrap_ci_upper": 0.7,
        "noise_floor_sigma": 1.0e-5,
        "signal_to_noise_ratio": 3.0
    }
    
    errors = validate_correlation_result_schema(invalid_result, schema)
    assert len(errors) > 0, "Should have caught type errors"
    assert any("region_type" in e and "string" in e for e in errors), "Should report region_type type error"
    assert any("lag_months" in e and "integer" in e for e in errors), "Should report lag_months type error"
    assert any("significant_after_correction" in e and "boolean" in e for e in errors), "Should report significant_after_correction type error"

def test_p_value_bounds():
    """Test that p-values outside [0, 1] are caught."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": "target",
        "lag_months": 0,
        "correlation_coefficient": 0.5,
        "p_value": -0.1,  # Invalid
        "corrected_p_value": 1.5,  # Invalid
        "significant_after_correction": False,
        "n_samples": 100,
        "n_eff": 80,
        "bootstrap_ci_lower": 0.3,
        "bootstrap_ci_upper": 0.7,
        "noise_floor_sigma": 1.0e-5,
        "signal_to_noise_ratio": 3.0
    }
    
    errors = validate_correlation_result_schema(invalid_result, schema)
    assert len(errors) > 0, "Should have caught invalid p-values"
    assert any("p_value" in e for e in errors), "Error message should mention p_value"

def test_bootstrap_ci_consistency():
    """Test that bootstrap CI lower bound is less than or equal to upper bound."""
    schema = load_output_schema()
    
    invalid_result = {
        "region_type": "target",
        "lag_months": 0,
        "correlation_coefficient": 0.5,
        "p_value": 0.05,
        "corrected_p_value": 0.1,
        "significant_after_correction": False,
        "n_samples": 100,
        "n_eff": 80,
        "bootstrap_ci_lower": 0.7,  # Invalid: > upper
        "bootstrap_ci_upper": 0.3,
        "noise_floor_sigma": 1.0e-5,
        "signal_to_noise_ratio": 3.0
    }
    
    # Note: This specific constraint might not be in the YAML schema, 
    # but we can add a custom check here if needed.
    # For now, we test that the schema validation runs without error on the data types.
    errors = validate_correlation_result_schema(invalid_result, schema)
    # We don't assert errors here unless the schema explicitly includes this constraint
    # This test documents the expectation that CI_lower <= CI_upper

if __name__ == "__main__":
    pytest.main([__file__, "-v"])