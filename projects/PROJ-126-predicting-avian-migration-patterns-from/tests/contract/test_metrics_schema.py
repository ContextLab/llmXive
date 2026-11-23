"""
Contract test for metrics output schema (US3).

Validates that the final metrics output file (data/processed/metrics.json)
contains all required keys, correct data types, and valid value ranges
as specified in the project requirements.

This test ensures:
1. All required top-level keys are present
2. Bootstrap confidence intervals have correct structure
3. P-values are within valid ranges [0, 1]
4. RMSE values are positive numbers
5. Correlation values are within [-1, 1]
"""
import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
METRICS_FILE = PROJECT_ROOT / "data" / "processed" / "metrics.json"

# Required schema definition
REQUIRED_KEYS = [
    "rmse_temp_only",
    "rmse_ndvi_only", 
    "rmse_combined",
    "correlation_temp_only",
    "correlation_ndvi_only",
    "correlation_combined",
    "ci_temp_vs_ndvi",
    "ci_combined_vs_temp",
    "p_value_combined_vs_temp",
    "bootstrap_iterations",
    "threshold_stability"
]

# Expected structure for confidence intervals
CI_SCHEMA = {
    "lower": float,
    "upper": float,
    "confidence_level": float
}

# Expected structure for threshold stability
THRESHOLD_STABILITY_SCHEMA = {
    "3": dict,
    "5": dict,
    "10": dict,
    "max_variation_days": float,
    "status": str
}

def load_metrics_file() -> Dict[str, Any]:
    """Load the metrics JSON file."""
    if not METRICS_FILE.exists():
        pytest.fail(f"Metrics file not found at {METRICS_FILE}. "
                   "Ensure T031 has been executed to generate metrics.json.")
    
    with open(METRICS_FILE, 'r') as f:
        return json.load(f)

def test_metrics_file_exists():
    """Contract test: Verify metrics file exists."""
    assert METRICS_FILE.exists(), f"Metrics file missing: {METRICS_FILE}"

def test_all_required_keys_present():
    """Contract test: Verify all required keys are present in metrics."""
    metrics = load_metrics_file()
    
    missing_keys = [key for key in REQUIRED_KEYS if key not in metrics]
    assert not missing_keys, f"Missing required keys in metrics: {missing_keys}"

def test_rmse_values_are_positive():
    """Contract test: Verify RMSE values are positive numbers."""
    metrics = load_metrics_file()
    
    rmse_keys = ["rmse_temp_only", "rmse_ndvi_only", "rmse_combined"]
    for key in rmse_keys:
        value = metrics.get(key)
        assert value is not None, f"RMSE key '{key}' is missing"
        assert isinstance(value, (int, float)), f"RMSE '{key}' is not a number: {type(value)}"
        assert value >= 0, f"RMSE '{key}' must be non-negative: {value}"

def test_correlation_values_in_range():
    """Contract test: Verify correlation values are within [-1, 1]."""
    metrics = load_metrics_file()
    
    corr_keys = ["correlation_temp_only", "correlation_ndvi_only", "correlation_combined"]
    for key in corr_keys:
        value = metrics.get(key)
        assert value is not None, f"Correlation key '{key}' is missing"
        assert isinstance(value, (int, float)), f"Correlation '{key}' is not a number: {type(value)}"
        assert -1.0 <= value <= 1.0, f"Correlation '{key}' out of range [-1, 1]: {value}"

def test_confidence_intervals_have_correct_structure():
    """Contract test: Verify CI structure matches expected schema."""
    metrics = load_metrics_file()
    
    ci_keys = ["ci_temp_vs_ndvi", "ci_combined_vs_temp"]
    for ci_key in ci_keys:
        ci = metrics.get(ci_key)
        assert ci is not None, f"CI key '{ci_key}' is missing"
        assert isinstance(ci, dict), f"CI '{ci_key}' is not a dict: {type(ci)}"
        
        # Check required fields in CI
        for field, expected_type in CI_SCHEMA.items():
            assert field in ci, f"CI '{ci_key}' missing field '{field}'"
            assert isinstance(ci[field], expected_type), \
                f"CI '{ci_key}.{field}' has wrong type: {type(ci[field])}"
        
        # Validate CI logic: lower <= upper
        assert ci["lower"] <= ci["upper"], \
            f"CI '{ci_key}' has invalid range: lower={ci['lower']}, upper={ci['upper']}"
        
        # Validate confidence level
        assert 0.0 <= ci["confidence_level"] <= 1.0, \
            f"CI '{ci_key}' confidence level out of range: {ci['confidence_level']}"

def test_p_value_in_valid_range():
    """Contract test: Verify p-value is within [0, 1]."""
    metrics = load_metrics_file()
    
    p_value = metrics.get("p_value_combined_vs_temp")
    assert p_value is not None, "P-value key 'p_value_combined_vs_temp' is missing"
    assert isinstance(p_value, (int, float)), \
        f"P-value is not a number: {type(p_value)}"
    assert 0.0 <= p_value <= 1.0, \
        f"P-value out of range [0, 1]: {p_value}"

def test_bootstrap_iterations_is_positive_integer():
    """Contract test: Verify bootstrap_iterations is a positive integer."""
    metrics = load_metrics_file()
    
    iterations = metrics.get("bootstrap_iterations")
    assert iterations is not None, "Key 'bootstrap_iterations' is missing"
    assert isinstance(iterations, int), \
        f"bootstrap_iterations is not an integer: {type(iterations)}"
    assert iterations > 0, f"bootstrap_iterations must be positive: {iterations}"

def test_threshold_stability_structure():
    """Contract test: Verify threshold stability section structure."""
    metrics = load_metrics_file()
    
    stability = metrics.get("threshold_stability")
    assert stability is not None, "Key 'threshold_stability' is missing"
    assert isinstance(stability, dict), \
        f"threshold_stability is not a dict: {type(stability)}"
    
    # Check threshold-specific entries
    for threshold in ["3", "5", "10"]:
        assert threshold in stability, f"Threshold '{threshold}' missing in stability"
        assert isinstance(stability[threshold], dict), \
            f"Threshold '{threshold}' entry is not a dict"
        
        # Each threshold should have mean and std
        ts = stability[threshold]
        assert "mean_days" in ts, f"Threshold '{threshold}' missing 'mean_days'"
        assert "std_days" in ts, f"Threshold '{threshold}' missing 'std_days'"
    
    # Check aggregate fields
    assert "max_variation_days" in stability, "Missing 'max_variation_days'"
    assert isinstance(stability["max_variation_days"], (int, float)), \
        f"max_variation_days is not a number: {type(stability['max_variation_days'])}"
    
    assert "status" in stability, "Missing 'status' in threshold_stability"
    assert stability["status"] in ["stable", "unstable"], \
        f"Invalid status value: {stability['status']}"

def test_ci_lower_bound_less_than_upper_bound():
    """Contract test: Verify all CIs have lower <= upper."""
    metrics = load_metrics_file()
    
    ci_keys = ["ci_temp_vs_ndvi", "ci_combined_vs_temp"]
    for ci_key in ci_keys:
        ci = metrics[ci_key]
        assert ci["lower"] <= ci["upper"], \
            f"Invalid CI range in {ci_key}: lower={ci['lower']}, upper={ci['upper']}"

def test_metrics_file_is_valid_json():
    """Contract test: Verify metrics file is valid JSON."""
    try:
        metrics = load_metrics_file()
        # If we got here, it's valid JSON
        assert isinstance(metrics, dict), "Root of metrics.json is not a dict"
    except json.JSONDecodeError as e:
        pytest.fail(f"metrics.json is not valid JSON: {e}")