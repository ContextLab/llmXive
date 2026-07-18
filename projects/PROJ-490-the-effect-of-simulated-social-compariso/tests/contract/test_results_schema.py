import pytest
import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validators import load_schema, validate_json_against_schema, assert_valid

CONTRACTS_DIR = project_root / "contracts"

@pytest.fixture
def results_schema():
    return load_schema(CONTRACTS_DIR / "results.schema.yaml")

@pytest.fixture
def valid_results():
    return {
        "data_path": "data/raw/synthetic_dataset.csv",
        "data_source_type": "synthetic",
        "model_summary": {
            "r_squared": 0.45,
            "adj_r_squared": 0.42,
            "f_statistic": 15.2,
            "f_p_value": 0.001,
            "coefficients": [
                {"term": "Intercept", "coefficient": 10.0, "std_error": 1.0, "p_value": 0.0, "ci_lower": 8.0, "ci_upper": 12.0},
                {"term": "avatar_condition", "coefficient": 2.5, "std_error": 0.5, "p_value": 0.01, "ci_lower": 1.5, "ci_upper": 3.5}
            ]
        },
        "assumption_checks": {
            "normality": {"test_name": "Shapiro-Wilk", "statistic": 0.98, "p_value": 0.5, "passed": True},
            "homoscedasticity": {"test_name": "Breusch-Pagan", "statistic": 1.2, "p_value": 0.3, "passed": True},
            "collinearity": {"vif_scores": {"avatar_condition": 1.1, "pre_self_esteem": 1.05}, "max_vif": 1.1, "passed": True}
        },
        "bootstrap_stability": {
            "interaction_ci_width_variance": 0.005,
            "iterations": 1000,
            "stable": True
        },
        "sensitivity_findings": {
            "parameter_recovery_error": 0.02,
            "threshold_stability": [
                {"threshold": 0.05, "stability_metric": 0.95}
            ],
            "error_correction_applied": False
        }
    }

def test_results_schema_validation(results_schema, valid_results):
    """Test that a valid results dict passes the results schema."""
    result = validate_json_against_schema(valid_results, results_schema)
    assert result["valid"], f"Schema validation failed: {result.get('errors')}"
    assert_valid(result)

def test_results_schema_missing_required(results_schema):
    """Test that a results dict missing a required field fails validation."""
    data = {
        "data_path": "data/raw/test.csv",
        # Missing data_source_type and other required fields
    }
    result = validate_json_against_schema(data, results_schema)
    assert not result["valid"]
