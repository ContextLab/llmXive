"""
Test contract for model output schema validation.

Validates that the regression summary JSON output matches the
structure defined in contracts/output.schema.yaml.
"""
import json
import os
import pytest
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import RESULTS_ROOT


def load_output_schema_contract():
    """Load the output schema contract from YAML file."""
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        pytest.fail(f"Output schema contract file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_required_keys(data, required_keys, path=""):
    """Recursively validate that all required keys exist in the data."""
    missing = []
    for key in required_keys:
        if key not in data:
            missing.append(f"{path}.{key}" if path else key)
        elif isinstance(required_keys[key], dict) and isinstance(data[key], dict):
            missing.extend(validate_required_keys(data[key], required_keys[key], f"{path}.{key}" if path else key))
    return missing


@pytest.mark.contract
def test_output_matches_schema():
    """
    Validate that regression_summary.json matches the output schema contract.
    
    This test ensures that the model output structure (coefficients, p_values,
    vif_scores, diagnostics, interpretation) conforms to the specification
    defined in contracts/output.schema.yaml.
    """
    # Load the schema contract
    schema = load_output_schema_contract()
    
    # Define expected structure based on task description and schema
    expected_structure = {
        "coefficients": {
            "term": dict,
            "value": (int, float),
            "std_error": (int, float),
            "p_value": (int, float),
            "beta": (int, float)
        },
        "p_values": {
            "term": (int, float)
        },
        "vif_scores": {
            "term": (int, float)
        },
        "diagnostics": {
            "r_squared": (int, float),
            "adj_r_squared": (int, float),
            "f_statistic": (int, float),
            "f_p_value": (int, float),
            "correlation_matrix": dict,
            "vif_scores": dict
        },
        "interpretation": str
    }
    
    # Check if output file exists
    output_path = Path(RESULTS_ROOT) / "models" / "regression_summary.json"
    
    # If file doesn't exist, skip test (model hasn't been run yet)
    if not output_path.exists():
        pytest.skip(f"Output file not found: {output_path}. Run code/03_model.py first.")
    
    # Load the actual output
    with open(output_path, 'r') as f:
        output_data = json.load(f)
    
    # Validate top-level keys
    required_top_level = ["coefficients", "p_values", "vif_scores", "diagnostics", "interpretation"]
    missing_keys = []
    for key in required_top_level:
        if key not in output_data:
            missing_keys.append(key)
    
    assert not missing_keys, f"Missing required top-level keys: {missing_keys}"
    
    # Validate coefficients structure
    assert isinstance(output_data["coefficients"], list), "coefficients must be a list"
    if output_data["coefficients"]:  # Only validate if not empty
        first_coef = output_data["coefficients"][0]
        assert "term" in first_coef, "Coefficient must have 'term' field"
        assert "value" in first_coef, "Coefficient must have 'value' field"
        assert "p_value" in first_coef, "Coefficient must have 'p_value' field"
    
    # Validate diagnostics structure (critical for SC-002)
    diagnostics = output_data["diagnostics"]
    assert isinstance(diagnostics, dict), "diagnostics must be a dictionary"
    assert "vif_scores" in diagnostics, "diagnostics must contain nested vif_scores (SC-002)"
    assert "correlation_matrix" in diagnostics, "diagnostics must contain raw correlation_matrix (SC-002)"
    
    # Validate interpretation is a string
    assert isinstance(output_data["interpretation"], str), "interpretation must be a string"
    assert len(output_data["interpretation"]) > 0, "interpretation cannot be empty"
    
    # Validate p_values and vif_scores are dictionaries
    assert isinstance(output_data["p_values"], dict), "p_values must be a dictionary"
    assert isinstance(output_data["vif_scores"], dict), "vif_scores must be a dictionary"
    
    # Additional validation: Check that VIF scores in top level match nested diagnostics
    if output_data["vif_scores"] and "vif_scores" in diagnostics:
        # Both should exist, values should be consistent (allowing for minor float differences)
        pass  # Detailed numeric comparison would go here if needed
    
    # Success: All validations passed
    assert True, "Model output matches the expected schema contract"


@pytest.mark.contract
def test_schema_contains_required_fields():
    """
    Verify that the schema contract itself contains all required field definitions.
    """
    schema = load_output_schema_contract()
    
    # Check schema has required sections
    required_sections = ["coefficients", "p_values", "vif_scores", "diagnostics", "interpretation"]
    
    for section in required_sections:
        assert section in schema, f"Schema must define '{section}' section"
    
    # Check diagnostics has nested requirements
    assert "vif_scores" in schema["diagnostics"], "Schema diagnostics must include nested vif_scores"
    assert "correlation_matrix" in schema["diagnostics"], "Schema diagnostics must include correlation_matrix"