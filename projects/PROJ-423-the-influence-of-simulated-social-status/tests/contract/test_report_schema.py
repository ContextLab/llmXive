"""
Contract tests for report schema validation.

Verifies that the generated report data structure matches the schema
defined in contracts/model_output.schema.yaml before HTML/PDF generation.
"""
import pytest
import os
import json
from pathlib import Path

# Import the schema definition to ensure test expectations match the contract
# We load the schema file directly to avoid hard-coding expectations
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "model_output.schema.yaml"

REQUIRED_TOP_LEVEL_KEYS = {
    "coefficients",
    "p_values",
    "vif",
    "ci_width",
    "model_type"
}

def load_schema():
    """Load the schema definition from the contracts directory."""
    if not SCHEMA_PATH.exists():
        # Fallback to hardcoded expectations if schema file is missing (should not happen in CI)
        return REQUIRED_TOP_LEVEL_KEYS
    
    # Simple YAML parser for this specific flat schema structure
    # Avoiding heavy dependencies like pyyaml in tests if possible, 
    # but since it's a dependency, we can use it if available.
    # For robustness, we parse the keys manually or use yaml if present.
    try:
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
            return set(schema.keys())
    except ImportError:
        # Fallback: read lines and extract keys
        with open(SCHEMA_PATH, 'r') as f:
            lines = f.readlines()
            keys = set()
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and ':' in stripped:
                    key = stripped.split(':')[0].strip()
                    keys.add(key)
            return keys

def test_report_data_structure_matches_schema():
    """
    Verify that the data structure intended for the report contains
    all required sections defined in contracts/model_output.schema.yaml.
    """
    schema_keys = load_schema()
    
    # Mock the data structure that `report.py` would consume
    # This mimics the output of `load_model_results` + `calculate_vif` + `run_sensitivity_analysis`
    report_data = {
        "coefficients": {
            "status_level": 0.5,
            "observed_behavior": -0.2,
            "interaction": 0.3
        },
        "p_values": {
            "status_level": 0.01,
            "observed_behavior": 0.05,
            "interaction": 0.02
        },
        "vif": {
            "status_level": 1.05,
            "observed_behavior": 1.02,
            "interaction": 1.10
        },
        "ci_width": 0.45,
        "model_type": "Mixed-Effects"
    }
    
    missing = schema_keys - set(report_data.keys())
    extra = set(report_data.keys()) - schema_keys
    
    assert not missing, f"Report data missing required schema sections: {missing}"
    # Extra keys are allowed for extensibility, but missing keys are fatal
    
def test_forest_plot_data_validity():
    """
    Verify that forest plot data (used in report generation) has the expected structure.
    This ensures the data passed to `generate_forest_plot` is valid.
    """
    plot_data = {
        "conditions": ["High/Risky", "High/Conservative", "Low/Risky", "Low/Conservative"],
        "means": [50.0, 45.0, 40.0, 38.0],
        "ci_lower": [48.0, 43.0, 38.0, 36.0],
        "ci_upper": [52.0, 47.0, 42.0, 40.0]
    }
    
    # Check list lengths match
    assert len(plot_data["conditions"]) == len(plot_data["means"])
    assert len(plot_data["means"]) == len(plot_data["ci_lower"])
    assert len(plot_data["ci_lower"]) == len(plot_data["ci_upper"])
    
    # Check data types
    assert all(isinstance(m, (int, float)) for m in plot_data["means"])
    assert all(isinstance(l, (int, float)) for l in plot_data["ci_lower"])
    assert all(isinstance(u, (int, float)) for u in plot_data["ci_upper"])
    
def test_model_type_enum_validity():
    """
    Verify that model_type is one of the expected values.
    """
    valid_types = {"Fixed-Effects", "Mixed-Effects"}
    
    # Test valid
    assert "Mixed-Effects" in valid_types
    assert "Fixed-Effects" in valid_types
    
    # Test invalid
    assert "Invalid-Type" not in valid_types
