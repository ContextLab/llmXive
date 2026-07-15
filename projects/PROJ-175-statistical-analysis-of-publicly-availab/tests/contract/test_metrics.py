"""
Contract test for evaluation metrics schema.

This test validates that the evaluation metrics produced by `code/evaluation/metrics.py`
conform to the expected schema defined in the project specifications.

It ensures:
1. The output file exists and is valid JSON.
2. The top-level keys match the expected structure (logistic, bayesian, comparison).
3. The nested metric dictionaries contain the required keys (auc, precision, recall, f1, calibration_slope, calibration_intercept).
4. All metric values are numeric and within valid ranges (e.g., AUC in [0, 1]).
5. The comparison section includes the Delta AUC and its confidence interval.
"""

import json
import os
import pytest
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
METRICS_OUTPUT_PATH = PROJECT_ROOT / "data" / "final" / "evaluation_metrics.json"

# Expected schema structure based on FR-009 and FR-010
EXPECTED_TOP_LEVEL_KEYS = {"logistic", "bayesian", "comparison"}

REQUIRED_METRIC_KEYS = {
    "auc",
    "precision",
    "recall",
    "f1",
    "calibration_slope",
    "calibration_intercept"
}

REQUIRED_COMPARISON_KEYS = {
    "delta_auc",
    "delta_auc_ci_lower",
    "delta_auc_ci_upper",
    "p_value_delong",
    "hypothesis_supported"
}


@pytest.fixture
def metrics_data():
    """Load the evaluation metrics JSON file."""
    if not METRICS_OUTPUT_PATH.exists():
        pytest.fail(
            f"Evaluation metrics file not found at {METRICS_OUTPUT_PATH}. "
            "Ensure code/evaluation/metrics.py and code/evaluation/report.py have been executed."
        )
    
    with open(METRICS_OUTPUT_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in metrics file: {e}")


def test_file_exists(metrics_data):
    """Contract: The metrics file must exist."""
    assert METRICS_OUTPUT_PATH.exists(), "Metrics file does not exist."


def test_top_level_keys(metrics_data):
    """Contract: The top-level structure must contain logistic, bayesian, and comparison."""
    missing_keys = EXPECTED_TOP_LEVEL_KEYS - set(metrics_data.keys())
    assert not missing_keys, f"Missing top-level keys in metrics schema: {missing_keys}"


def _validate_model_metrics(model_name: str, data: dict):
    """Helper to validate a model's metric block."""
    assert model_name in data, f"Model '{model_name}' not found in metrics."
    model_data = data[model_name]
    
    missing_keys = REQUIRED_METRIC_KEYS - set(model_data.keys())
    assert not missing_keys, f"Missing metric keys for {model_name}: {missing_keys}"

    # Validate ranges
    assert 0.0 <= model_data["auc"] <= 1.0, f"AUC for {model_name} out of bounds [0, 1]"
    assert 0.0 <= model_data["precision"] <= 1.0, f"Precision for {model_name} out of bounds [0, 1]"
    assert 0.0 <= model_data["recall"] <= 1.0, f"Recall for {model_name} out of bounds [0, 1]"
    assert 0.0 <= model_data["f1"] <= 1.0, f"F1 for {model_name} out of bounds [0, 1]"
    
    # Calibration slope/intercept can be negative, but should be numeric
    assert isinstance(model_data["calibration_slope"], (int, float)), f"calibration_slope for {model_name} is not numeric"
    assert isinstance(model_data["calibration_intercept"], (int, float)), f"calibration_intercept for {model_name} is not numeric"


def test_logistic_metrics_schema(metrics_data):
    """Contract: Validate the logistic regression metrics structure and values."""
    _validate_model_metrics("logistic", metrics_data)


def test_bayesian_metrics_schema(metrics_data):
    """Contract: Validate the Bayesian model metrics structure and values."""
    _validate_model_metrics("bayesian", metrics_data)


def test_comparison_metrics_schema(metrics_data):
    """Contract: Validate the comparison metrics structure (Delta AUC, CI, p-value)."""
    assert "comparison" in metrics_data, "Comparison section missing."
    comparison_data = metrics_data["comparison"]
    
    missing_keys = REQUIRED_COMPARISON_KEYS - set(comparison_data.keys())
    assert not missing_keys, f"Missing comparison keys: {missing_keys}"

    # Validate numeric types
    assert isinstance(comparison_data["delta_auc"], (int, float)), "delta_auc must be numeric"
    assert isinstance(comparison_data["delta_auc_ci_lower"], (int, float)), "delta_auc_ci_lower must be numeric"
    assert isinstance(comparison_data["delta_auc_ci_upper"], (int, float)), "delta_auc_ci_upper must be numeric"
    assert isinstance(comparison_data["p_value_delong"], (int, float)), "p_value_delong must be numeric"
    
    # Validate hypothesis_supported is boolean
    assert isinstance(comparison_data["hypothesis_supported"], bool), "hypothesis_supported must be boolean"

    # Logical consistency: CI should be ordered
    assert comparison_data["delta_auc_ci_lower"] <= comparison_data["delta_auc_ci_upper"], \
        "Confidence interval lower bound must be <= upper bound"


def test_metrics_precision(metrics_data):
    """Contract: Ensure metrics are stored with sufficient precision (at least 4 decimal places)."""
    def check_precision(value, name):
        # Convert to string and check decimal places
        s_val = f"{value:.10f}"
        if '.' in s_val:
            decimals = len(s_val.split('.')[1].rstrip('0'))
            assert decimals >= 4, f"{name} lacks sufficient precision: {value}"

    check_precision(metrics_data["logistic"]["auc"], "logistic auc")
    check_precision(metrics_data["bayesian"]["auc"], "bayesian auc")
    check_precision(metrics_data["comparison"]["delta_auc"], "delta_auc")