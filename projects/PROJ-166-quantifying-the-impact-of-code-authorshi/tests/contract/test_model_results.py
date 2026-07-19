import json
import os
import pytest
from pathlib import Path

# Path to the expected output file
OUTPUT_FILE = Path("data/processed/model_results.json")

def test_model_results_schema():
    """
    Contract test for model results schema.
    Verifies that the output JSON contains required keys and data types.
    """
    if not OUTPUT_FILE.exists():
        pytest.fail(f"Output file {OUTPUT_FILE} does not exist. Run fit_models.py first.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    # Check top-level keys
    required_keys = [
        "convergence_status",
        "coefficients",
        "standard_errors",
        "p_values",
        "confidence_intervals",
        "adjusted_p_values",
        "vif_metrics"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Check types
    assert isinstance(data["convergence_status"], bool), "convergence_status must be a boolean"
    assert isinstance(data["coefficients"], dict), "coefficients must be a dict"
    assert isinstance(data["standard_errors"], dict), "standard_errors must be a dict"
    assert isinstance(data["p_values"], dict), "p_values must be a dict"
    assert isinstance(data["confidence_intervals"], dict), "confidence_intervals must be a dict"
    assert isinstance(data["adjusted_p_values"], dict), "adjusted_p_values must be a dict"
    assert isinstance(data["vif_metrics"], dict), "vif_metrics must be a dict"
    
    # Check that coefficients are floats
    for key, val in data["coefficients"].items():
        assert isinstance(val, (int, float)), f"Coefficient for {key} must be numeric"
    
    # Check that standard errors are floats
    for key, val in data["standard_errors"].items():
        assert isinstance(val, (int, float)), f"Standard error for {key} must be numeric"
    
    # Check that p-values are floats and between 0 and 1
    for key, val in data["p_values"].items():
        assert isinstance(val, (int, float)), f"P-value for {key} must be numeric"
        assert 0 <= val <= 1, f"P-value for {key} must be between 0 and 1"
    
    # Check that adjusted p-values are floats and between 0 and 1
    for key, val in data["adjusted_p_values"].items():
        assert isinstance(val, (int, float)), f"Adjusted p-value for {key} must be numeric"
        assert 0 <= val <= 1, f"Adjusted p-value for {key} must be between 0 and 1"
    
    # Check confidence intervals are lists of two floats
    for key, val in data["confidence_intervals"].items():
        assert isinstance(val, list), f"Confidence interval for {key} must be a list"
        assert len(val) == 2, f"Confidence interval for {key} must have 2 elements"
        assert all(isinstance(x, (int, float)) for x in val), f"Confidence interval elements for {key} must be numeric"
        assert val[0] <= val[1], f"Confidence interval lower bound must be <= upper bound for {key}"
    
    # Check VIF metrics are floats
    for key, val in data["vif_metrics"].items():
        assert isinstance(val, (int, float, type(None))), f"VIF for {key} must be numeric or None"

def test_author_count_coefficient_exists():
    """
    Verify that the author_count_coefficient (unique_authors) exists in the results.
    """
    if not OUTPUT_FILE.exists():
        pytest.skip(f"Output file {OUTPUT_FILE} does not exist.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    # The model uses 'unique_authors' as a predictor
    assert "unique_authors" in data["coefficients"], "Missing 'unique_authors' coefficient"
    assert "unique_authors" in data["standard_errors"], "Missing 'unique_authors' standard error"
    assert "unique_authors" in data["p_values"], "Missing 'unique_authors' p-value"
    assert "unique_authors" in data["confidence_intervals"], "Missing 'unique_authors' confidence interval"
    assert "unique_authors" in data["adjusted_p_values"], "Missing 'unique_authors' adjusted p-value"

def test_convergence_status_flagged():
    """
    Verify that convergence_status is a boolean and reflects the model state.
    """
    if not OUTPUT_FILE.exists():
        pytest.skip(f"Output file {OUTPUT_FILE} does not exist.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data["convergence_status"], bool), "convergence_status must be a boolean"
    # If it's False, we expect a message or at least the flag to be clear
    if not data["convergence_status"]:
        # Log or assert that there's an indication of failure (optional, but good practice)
        pass
