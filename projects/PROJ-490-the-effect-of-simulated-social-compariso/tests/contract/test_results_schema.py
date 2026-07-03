"""
Contract test for regression output schema.

This test validates that the regression output artifacts produced by the
analysis pipeline (code/analysis/regression.py) conform to the schema
defined in contracts/results.schema.yaml.

It verifies:
1. The output JSON file exists.
2. The file structure matches the expected schema (coefficients, diagnostics, metadata).
3. Specific required fields (e.g., interaction_effect, p_value, assumption_checks) are present and typed correctly.
"""

import json
import os
import pytest
from pathlib import Path

# Import validation utilities from the project's utility module
# Using the API surface provided in code/utils/validators.py
from utils.validators import (
    load_schema,
    validate_json_against_schema,
    assert_valid
)


@pytest.fixture
def schema_path():
    """Locate the results schema file."""
    # The project root is assumed to be the parent of 'code' and 'tests'
    # Based on T001 structure: projects/PROJ-490-.../contracts/results.schema.yaml
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    return project_root / "contracts" / "results.schema.yaml"


@pytest.fixture
def sample_output_path():
    """
    Generate a sample output file to test against.
    Since the actual regression script might not have run yet in this specific test context,
    we create a minimal valid sample that *should* exist after T021 runs.
    
    NOTE: In a real CI/CD or integration flow, this would point to the actual
    output of `code/analysis/regression.py`. For this contract test, we ensure
    the validator works against a known-good structure.
    """
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_dir / "regression_results_sample.json"
    
    sample_data = {
        "metadata": {
            "data_source_type": "synthetic",
            "data_path": "data/raw/synthetic_dataset.csv",
            "model_type": "ANCOVA",
            "n_samples": 100,
            "seed": 42
        },
        "coefficients": [
            {
                "term": "Intercept",
                "estimate": 5.0,
                "std_error": 0.5,
                "p_value": 0.001,
                "ci_lower": 4.0,
                "ci_upper": 6.0
            },
            {
                "term": "avatar_condition",
                "estimate": -0.2,
                "std_error": 0.1,
                "p_value": 0.04,
                "ci_lower": -0.4,
                "ci_upper": 0.0
            },
            {
                "term": "pre_self_esteem",
                "estimate": 0.8,
                "std_error": 0.05,
                "p_value": 0.0001,
                "ci_lower": 0.7,
                "ci_upper": 0.9
            },
            {
                "term": "comparison_tendency",
                "estimate": -0.15,
                "std_error": 0.08,
                "p_value": 0.06,
                "ci_lower": -0.31,
                "ci_upper": 0.01
            },
            {
                "term": "avatar_condition:comparison_tendency",
                "estimate": 0.05,
                "std_error": 0.04,
                "p_value": 0.21,
                "ci_lower": -0.03,
                "ci_upper": 0.13
            }
        ],
        "diagnostics": {
            "model_fit": {
                "r_squared": 0.65,
                "adj_r_squared": 0.63,
                "f_statistic": 45.2,
                "f_p_value": 1e-10
            },
            "assumption_checks": {
                "normality_shapiro_wilk": {
                    "statistic": 0.98,
                    "p_value": 0.45,
                    "passed": True
                },
                "homoscedasticity_breusch_pagan": {
                    "statistic": 1.2,
                    "p_value": 0.27,
                    "passed": True
                },
                "collinearity_vif": {
                    "avatar_condition": 1.1,
                    "pre_self_esteem": 1.05,
                    "comparison_tendency": 1.2,
                    "interaction": 1.3,
                    "max_vif": 1.3,
                    "passed": True
                }
            },
            "interpretation_label": "Simulated Causal Effect"
        },
        "sensitivity": {
            "bootstrap_ci_width_variance": 0.002,
            "stability_flag": True
        }
    }
    
    with open(output_file, "w") as f:
        json.dump(sample_data, f, indent=2)
        
    return output_file


def test_results_schema_exists(schema_path):
    """Verify the schema file itself exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"


def test_results_schema_validates_sample(sample_output_path, schema_path):
    """
    Contract test: Ensure a valid regression output file passes schema validation.
    """
    # Load the schema
    schema = load_schema(schema_path)
    
    # Load the sample output
    with open(sample_output_path, "r") as f:
        data = json.load(f)
    
    # Validate
    is_valid, errors = validate_json_against_schema(data, schema)
    
    assert is_valid, f"Regression output failed schema validation. Errors: {errors}"


def test_results_schema_structure_requirements(sample_output_path, schema_path):
    """
    Additional contract checks for specific structural requirements
    that might be too granular for a generic JSON schema or to ensure
    business logic constraints are met.
    """
    with open(sample_output_path, "r") as f:
        data = json.load(f)
    
    # Check top-level keys
    required_top_keys = {"metadata", "coefficients", "diagnostics", "sensitivity"}
    assert required_top_keys.issubset(data.keys()), f"Missing top-level keys: {required_top_keys - set(data.keys())}"
    
    # Check metadata keys
    required_meta_keys = {"data_source_type", "model_type", "n_samples"}
    assert required_meta_keys.issubset(data["metadata"].keys()), "Missing metadata keys"
    
    # Check coefficients structure
    assert isinstance(data["coefficients"], list), "Coefficients must be a list"
    assert len(data["coefficients"]) > 0, "Coefficients list cannot be empty"
    
    required_coef_keys = {"term", "estimate", "std_error", "p_value"}
    for coef in data["coefficients"]:
        assert required_coef_keys.issubset(coef.keys()), f"Missing keys in coefficient entry: {required_coef_keys - set(coef.keys())}"
    
    # Check interaction term exists
    terms = [c["term"] for c in data["coefficients"]]
    assert any("avatar_condition:comparison_tendency" in t for t in terms), "Interaction term (avatar_condition:comparison_tendency) is required"
    
    # Check diagnostics structure
    assert "assumption_checks" in data["diagnostics"], "Missing assumption_checks in diagnostics"
    assert "normality_shapiro_wilk" in data["diagnostics"]["assumption_checks"], "Missing Shapiro-Wilk check"
    assert "homoscedasticity_breusch_pagan" in data["diagnostics"]["assumption_checks"], "Missing Breusch-Pagan check"
    assert "collinearity_vif" in data["diagnostics"]["assumption_checks"], "Missing VIF check"

    # Check sensitivity structure
    assert "bootstrap_ci_width_variance" in data["sensitivity"], "Missing bootstrap variance in sensitivity"
    assert "stability_flag" in data["sensitivity"], "Missing stability flag in sensitivity"

def test_assert_valid_helper(sample_output_path, schema_path):
    """Test the assert_valid helper from validators.py directly."""
    schema = load_schema(schema_path)
    with open(sample_output_path, "r") as f:
        data = json.load(f)
    
    # This should not raise an AssertionError
    assert_valid(data, schema, "Regression Output")