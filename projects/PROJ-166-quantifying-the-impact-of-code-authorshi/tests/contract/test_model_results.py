import json
import os
import pytest
from pathlib import Path

# Path to the expected output file
# Note: The task description references model_results.json, but T017 specifies
# model_results_raw.json as the output. We test for the existence of the file
# produced by T017. If T017 is not run, this test will fail/skip appropriately.
OUTPUT_FILE = Path("data/processed/model_results_raw.json")

def test_model_results_schema():
    """
    Contract test for model results schema.
    Verifies that the output JSON contains required keys and data types
    as defined in the project specification for T017.
    """
    if not OUTPUT_FILE.exists():
        pytest.fail(f"Output file {OUTPUT_FILE} does not exist. Run code/analysis/fit_models.py first.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    # Check top-level keys required by T017 spec
    required_keys = [
        "author_count_coefficient",
        "std_err",
        "p_value",
        "ci_95_lower",
        "ci_95_upper",
        "vif",
        "convergence_status",
        "model_type"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Check types based on T017 specification
    assert isinstance(data["convergence_status"], bool), "convergence_status must be a boolean"
    assert data["model_type"] == "NegativeBinomial", "model_type must be 'NegativeBinomial'"
    
    # Check numeric fields
    assert isinstance(data["author_count_coefficient"], (int, float)), "author_count_coefficient must be numeric"
    assert isinstance(data["std_err"], (int, float)), "std_err must be numeric"
    assert isinstance(data["p_value"], (int, float)), "p_value must be numeric"
    assert 0 <= data["p_value"] <= 1, "p_value must be between 0 and 1"
    
    # Check CI is a list of two floats
    assert isinstance(data["ci_95_lower"], (int, float)), "ci_95_lower must be numeric"
    assert isinstance(data["ci_95_upper"], (int, float)), "ci_95_upper must be numeric"
    assert data["ci_95_lower"] <= data["ci_95_upper"], "CI lower bound must be <= upper bound"
    
    # Check VIF is a dict
    assert isinstance(data["vif"], dict), "vif must be a dict"
    for key, val in data["vif"].items():
        assert isinstance(val, (int, float)), f"VIF value for {key} must be numeric"

def test_author_count_coefficient_exists():
    """
    Verify that the author_count_coefficient (unique_authors) exists in the results.
    """
    if not OUTPUT_FILE.exists():
        pytest.skip(f"Output file {OUTPUT_FILE} does not exist.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    # The model uses 'unique_authors' as a predictor, output as author_count_coefficient
    assert "author_count_coefficient" in data, "Missing 'author_count_coefficient' key"
    assert "std_err" in data, "Missing 'std_err' key"
    assert "p_value" in data, "Missing 'p_value' key"
    assert "ci_95_lower" in data, "Missing 'ci_95_lower' key"
    assert "ci_95_upper" in data, "Missing 'ci_95_upper' key"

def test_convergence_status_flagged():
    """
    Verify that convergence_status is a boolean and reflects the model state.
    """
    if not OUTPUT_FILE.exists():
        pytest.skip(f"Output file {OUTPUT_FILE} does not exist.")
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data["convergence_status"], bool), "convergence_status must be a boolean"
    
    # If convergence failed, we expect the coefficients to be valid numbers (if the model
    # partially converged) or the status to be False. The spec says if it fails to converge,
    # log ERROR and set status to false. We verify the flag is present.
    if not data["convergence_status"]:
        # In a strict implementation, we might check if coefficients are None or NaN,
        # but the spec says output the results with status=False.
        pass