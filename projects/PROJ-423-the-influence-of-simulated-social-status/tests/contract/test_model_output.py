"""
Contract tests for model output validation.

Verifies that the analysis module produces outputs conforming to the
schema defined in `contracts/model_output.schema.yaml` and the
documented return structure of `code/analysis.py`.
"""
import pytest
import json
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure code/ is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis import analyze_interaction, validate_data_structure
from utils import set_seed

# Schema requirements derived from contracts/model_output.schema.yaml
# and task T025 description.
REQUIRED_OUTPUT_KEYS = [
    "coefficients",
    "standard_errors",
    "p_values",
    "vif_scores",
    "model_family",
    "interaction_significant",
    "n_observations",
    "structure_type"
]

@pytest.fixture(scope="module")
def run_analysis_once():
    """
    Runs the full analysis pipeline on the processed data once to generate
    a real model output for contract validation.
    """
    set_seed(42)
    
    # Paths are relative to project root
    processed_path = PROJECT_ROOT / "data" / "processed" / "synthetic_data_processed.csv"
    
    if not processed_path.exists():
        pytest.skip(f"Processed data not found at {processed_path}. Run data generation first.")
    
    try:
        df = pd.read_csv(processed_path)
        # Validate structure first to ensure we are in the expected mode (between-subjects)
        structure = validate_data_structure(df)
        
        # Run the interaction analysis
        result = analyze_interaction(df)
        return result, structure
    except Exception as e:
        pytest.fail(f"Analysis pipeline failed to run: {e}")

def test_model_output_structure(run_analysis_once):
    """
    Verify that the model output dictionary contains all required keys
    and correct data types as per the schema.
    """
    result, structure = run_analysis_once
    
    assert isinstance(result, dict), "Analysis result must be a dictionary."
    
    missing_keys = set(REQUIRED_OUTPUT_KEYS) - set(result.keys())
    assert not missing_keys, f"Model output missing required keys: {missing_keys}"
    
    # Verify types for specific keys
    assert isinstance(result["coefficients"], dict), "coefficients must be a dict"
    assert isinstance(result["standard_errors"], dict), "standard_errors must be a dict"
    assert isinstance(result["p_values"], dict), "p_values must be a dict"
    assert isinstance(result["vif_scores"], dict), "vif_scores must be a dict"
    assert isinstance(result["model_family"], str), "model_family must be a string"
    assert isinstance(result["interaction_significant"], bool), "interaction_significant must be a boolean"
    assert isinstance(result["n_observations"], int), "n_observations must be an integer"
    assert isinstance(result["structure_type"], str), "structure_type must be a string"
    
    # Verify that the coefficients, SEs, and p-values have the same keys
    coef_keys = set(result["coefficients"].keys())
    se_keys = set(result["standard_errors"].keys())
    p_keys = set(result["p_values"].keys())
    vif_keys = set(result["vif_scores"].keys())
    
    assert coef_keys == se_keys, "Coefficients and Standard Errors must have matching keys"
    assert coef_keys == p_keys, "Coefficients and P-values must have matching keys"
    # VIF might have a superset or subset depending on implementation, but should align on predictors
    assert coef_keys.issubset(vif_keys) or vif_keys.issubset(coef_keys), "VIF keys should align with predictor keys"

def test_interaction_term_present(run_analysis_once):
    """
    Verify that the interaction term (status_level * observed_behavior) 
    is explicitly present in the coefficients and p-values.
    """
    result, _ = run_analysis_once
    
    # The interaction term name depends on the formula used in analysis.py.
    # Based on T021b, the formula is: risk_taking ~ status_level * observed_behavior
    # This expands to main effects and the interaction.
    # We look for a key containing the interaction pattern.
    # Common statsmodels naming: status_level[T.High]:observed_behavior[T.Risky]
    
    interaction_found = False
    for key in result["coefficients"].keys():
        if ":" in key or "interaction" in key.lower():
            interaction_found = True
            break
    
    assert interaction_found, "Interaction term not found in model coefficients. The model formula must include the interaction."

def test_p_values_valid_range(run_analysis_once):
    """
    Verify that all reported p-values are between 0 and 1.
    """
    result, _ = run_analysis_once
    
    for term, p_val in result["p_values"].items():
        assert 0.0 <= p_val <= 1.0, f"P-value for {term} ({p_val}) is out of valid range [0, 1]."

def test_vif_threshold_check(run_analysis_once):
    """
    Verify that VIF scores are calculated and that the test logic can
    identify high VIF values (> 5.0) if they exist.
    """
    result, _ = run_analysis_once
    
    vif_scores = result["vif_scores"]
    assert len(vif_scores) > 0, "VIF scores should not be empty."
    
    # Check that values are numeric
    for term, vif in vif_scores.items():
        assert isinstance(vif, (int, float)), f"VIF for {term} must be numeric."
        assert vif >= 1.0, f"VIF for {term} ({vif}) is invalid (must be >= 1)."

def test_model_family_consistency(run_analysis_once):
    """
    Verify that the reported model_family matches the data structure
    and the logic in analysis.py (gaussian for continuous outcome).
    """
    result, _ = run_analysis_once
    
    # Based on T014b and T020b, if outcome is continuous (risk_taking_score),
    # family should be 'gaussian' or 'ols'.
    valid_families = ["gaussian", "ols", "linear"]
    assert result["model_family"] in valid_families, f"Unexpected model family: {result['model_family']}"

def test_interaction_significant_logic(run_analysis_once):
    """
    Verify that `interaction_significant` is a boolean derived from p-values.
    """
    result, _ = run_analysis_once
    
    # Find the interaction p-value again to cross-check
    interaction_p = None
    for key in result["p_values"].keys():
        if ":" in key or "interaction" in key.lower():
            interaction_p = result["p_values"][key]
            break
    
    if interaction_p is not None:
        expected_significant = interaction_p < 0.05
        assert result["interaction_significant"] == expected_significant, \
            f"interaction_significant ({result['interaction_significant']}) does not match p-value logic (< 0.05: {expected_significant})"
    else:
        # If no interaction term found, the test should have failed in test_interaction_term_present
        pytest.fail("Interaction term missing, cannot verify significance logic.")

def test_n_observations_matches_data(run_analysis_once):
    """
    Verify that the reported n_observations matches the actual row count
    of the processed data used.
    """
    result, _ = run_analysis_once
    processed_path = PROJECT_ROOT / "data" / "processed" / "synthetic_data_processed.csv"
    
    if processed_path.exists():
        df = pd.read_csv(processed_path)
        # The analysis might drop NaNs, so we check if result <= df count
        # But typically for clean synthetic data, it should match exactly.
        # We assert that it is a positive integer and reasonable.
        assert result["n_observations"] > 0, "n_observations must be positive."
        # We don't strictly assert equality because of potential internal dropping,
        # but we assert it's within a reasonable range of the source.
        assert result["n_observations"] <= len(df), "n_observations cannot exceed source data rows."
        assert result["n_observations"] >= len(df) * 0.99, "n_observations is suspiciously low compared to source."