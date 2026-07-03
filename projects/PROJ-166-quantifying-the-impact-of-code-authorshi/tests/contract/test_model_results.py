"""
Contract test for model results schema (US2).

Validates that the output of code/analysis/fit_models.py adheres to the
expected JSON schema defined in the project specifications.

This test ensures:
1. The file exists at data/processed/model_results.json
2. The root structure contains required keys: 'coefficients', 'vif_metrics', 'convergence_status'
3. The 'coefficients' list contains dictionaries with required fields:
   - term (str)
   - estimate (float)
   - std_err (float)
   - p_value (float)
   - p_value_adj (float)
   - conf_int_lower (float)
   - conf_int_upper (float)
4. 'convergence_status' is a boolean
5. 'vif_metrics' is a dictionary mapping term names to float VIF values
"""
import json
import os
import pytest
from pathlib import Path

# Import config to ensure we use the correct paths defined in the project
from code.config import ensure_directories

RESULTS_PATH = Path("data/processed/model_results.json")

def load_results():
    """Load the model results JSON file."""
    if not RESULTS_PATH.exists():
        pytest.fail(f"Results file not found at {RESULTS_PATH}. Run the pipeline first.")
    
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)

def test_file_exists():
    """Assert the output file exists."""
    assert RESULTS_PATH.exists(), f"Output file {RESULTS_PATH} does not exist. Run fit_models.py first."

def test_root_keys_present():
    """Assert the root level contains required keys."""
    data = load_results()
    
    required_keys = ["coefficients", "vif_metrics", "convergence_status"]
    missing = [k for k in required_keys if k not in data]
    
    assert not missing, f"Missing required root keys in model results: {missing}"

def test_convergence_status_type():
    """Assert convergence_status is a boolean."""
    data = load_results()
    assert isinstance(data["convergence_status"], bool), "convergence_status must be a boolean"

def test_vif_metrics_structure():
    """Assert vif_metrics is a dict of floats."""
    data = load_results()
    
    vif = data["vif_metrics"]
    assert isinstance(vif, dict), "vif_metrics must be a dictionary"
    
    for term, value in vif.items():
        assert isinstance(term, str), f"VIF key '{term}' must be a string"
        assert isinstance(value, (int, float)), f"VIF value for '{term}' must be numeric"
        assert value > 0, f"VIF value for '{term}' must be positive"

def test_coefficients_structure():
    """Assert coefficients list has correct structure and types."""
    data = load_results()
    coeffs = data["coefficients"]
    
    assert isinstance(coeffs, list), "coefficients must be a list"
    assert len(coeffs) > 0, "coefficients list cannot be empty"
    
    required_fields = [
        "term", "estimate", "std_err", "p_value", 
        "p_value_adj", "conf_int_lower", "conf_int_upper"
    ]
    
    for i, row in enumerate(coeffs):
        assert isinstance(row, dict), f"Coefficient entry {i} must be a dictionary"
        
        missing_fields = [f for f in required_fields if f not in row]
        assert not missing_fields, f"Coefficient entry {i} missing fields: {missing_fields}"
        
        # Type checks
        assert isinstance(row["term"], str), f"Entry {i}: 'term' must be string"
        assert isinstance(row["estimate"], (int, float)), f"Entry {i}: 'estimate' must be numeric"
        assert isinstance(row["std_err"], (int, float)), f"Entry {i}: 'std_err' must be numeric"
        assert isinstance(row["p_value"], (int, float)), f"Entry {i}: 'p_value' must be numeric"
        assert isinstance(row["p_value_adj"], (int, float)), f"Entry {i}: 'p_value_adj' must be numeric"
        assert isinstance(row["conf_int_lower"], (int, float)), f"Entry {i}: 'conf_int_lower' must be numeric"
        assert isinstance(row["conf_int_upper"], (int, float)), f"Entry {i}: 'conf_int_upper' must be numeric"
        
        # Value constraints
        assert row["std_err"] >= 0, f"Entry {i}: 'std_err' cannot be negative"
        assert 0 <= row["p_value"] <= 1, f"Entry {i}: 'p_value' must be between 0 and 1"
        assert 0 <= row["p_value_adj"] <= 1, f"Entry {i}: 'p_value_adj' must be between 0 and 1"
        assert row["conf_int_lower"] <= row["conf_int_upper"], f"Entry {i}: Lower CI must be <= Upper CI"

def test_author_count_coefficient_exists():
    """Assert that the author_count coefficient is present in the results."""
    data = load_results()
    terms = [row["term"] for row in data["coefficients"]]
    
    # The task description specifies 'author_count' as the primary predictor
    # We check for a term that looks like the author count predictor
    # It might be named 'author_count' or similar depending on the model formula
    author_terms = [t for t in terms if "author" in t.lower()]
    
    assert len(author_terms) > 0, (
        "No coefficient found for author diversity metric. "
        "The model must include an author count or entropy predictor."
    )

def test_model_results_is_valid_json():
    """Sanity check that the file is valid JSON (redundant with load but explicit)."""
    try:
        with open(RESULTS_PATH, "r") as f:
            json.load(f)
        assert True
    except json.JSONDecodeError as e:
        pytest.fail(f"Results file is not valid JSON: {e}")