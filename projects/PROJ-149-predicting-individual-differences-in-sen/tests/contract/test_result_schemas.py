import os
import json
import yaml
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Import config to get paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import get_path

def load_schema() -> Dict[str, Any]:
    """Load the YAML schema definition."""
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "result_schema.schema.yaml"
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_model_results() -> None:
    """Validate data/processed/model_results.json against ModelResults schema."""
    schema = load_schema()["components"]["schemas"]["ModelResults"]
    path = get_path("data/processed/model_results.json")
    
    assert os.path.exists(path), f"File not found: {path}"
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Check required fields
    for field in schema["required"]:
        assert field in data, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(data["adjusted_r2"], (int, float)), "adjusted_r2 must be numeric"
    assert isinstance(data["optimal_lambda"], (int, float)), "optimal_lambda must be numeric"
    assert isinstance(data["rmse"], (int, float)), "rmse must be numeric"
    assert isinstance(data["test_r2"], (int, float)), "test_r2 must be numeric"
    assert isinstance(data["test_rmse"], (int, float)), "test_rmse must be numeric"
    
    # Check optional post_hoc_power_analysis if present
    if "post_hoc_power_analysis" in data:
        power_data = data["post_hoc_power_analysis"]
        assert isinstance(power_data, dict), "post_hoc_power_analysis must be an object"
        for field in ["required_n", "power", "effect_size"]:
            assert field in power_data, f"Missing post-hoc field: {field}"
            assert isinstance(power_data[field], (int, float)), f"{field} must be numeric"

def validate_correlations_corrected() -> None:
    """Validate data/processed/correlations_corrected.csv against CorrelationsCorrected schema."""
    path = get_path("data/processed/correlations_corrected.csv")
    
    assert os.path.exists(path), f"File not found: {path}"
    
    df = pd.read_csv(path)
    
    # Check required columns
    required_cols = ["band", "r_value", "p_value", "p_value_corrected", "significant"]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check band values
    valid_bands = ["delta", "theta", "alpha", "low_beta", "high_beta", "gamma"]
    for band in df["band"]:
        assert band in valid_bands, f"Invalid band value: {band}"
    
    # Check numeric ranges
    assert all(df["r_value"].between(-1, 1)), "r_value must be between -1 and 1"
    assert all(df["p_value"].between(0, 1)), "p_value must be between 0 and 1"
    assert all(df["p_value_corrected"].between(0, 1)), "p_value_corrected must be between 0 and 1"
    assert all(df["significant"].isin([True, False, 0, 1])), "significant must be boolean"

def validate_non_linear_comparison() -> None:
    """Validate data/processed/non_linear_comparison.json against NonLinearComparison schema."""
    schema = load_schema()["components"]["schemas"]["NonLinearComparison"]
    path = get_path("data/processed/non_linear_comparison.json")
    
    assert os.path.exists(path), f"File not found: {path}"
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Check required fields
    for field in schema["required"]:
        assert field in data, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(data["linear_adjusted_r2"], (int, float)), "linear_adjusted_r2 must be numeric"
    assert isinstance(data["polynomial_adjusted_r2"], (int, float)), "polynomial_adjusted_r2 must be numeric"
    assert isinstance(data["f_statistic"], (int, float)), "f_statistic must be numeric"
    assert isinstance(data["p_value"], (int, float)), "p_value must be numeric"
    assert isinstance(data["significant_at_0p05"], bool), "significant_at_0p05 must be boolean"
    assert isinstance(data["interpretation"], str), "interpretation must be a string"

def validate_permutation_results() -> None:
    """Validate data/processed/permutation_results.json against PermutationResults schema."""
    schema = load_schema()["components"]["schemas"]["PermutationResults"]
    path = get_path("data/processed/permutation_results.json")
    
    assert os.path.exists(path), f"File not found: {path}"
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Check required fields
    for field in schema["required"]:
        assert field in data, f"Missing required field: {field}"
    
    # Check types
    assert isinstance(data["observed_r2"], (int, float)), "observed_r2 must be numeric"
    assert isinstance(data["p_value"], (int, float)), "p_value must be numeric"
    assert isinstance(data["null_distribution_path"], str), "null_distribution_path must be a string"
    
    # Verify the null distribution file exists if path is provided
    null_path = data["null_distribution_path"]
    if null_path and os.path.exists(null_path):
        import numpy as np
        null_data = np.load(null_path)
        assert isinstance(null_data, np.ndarray), "Null distribution must be a numpy array"
        assert len(null_data) > 0, "Null distribution cannot be empty"

# Test functions
def test_model_results_schema():
    validate_model_results()

def test_correlations_corrected_schema():
    validate_correlations_corrected()

def test_non_linear_comparison_schema():
    validate_non_linear_comparison()

def test_permutation_results_schema():
    validate_permutation_results()

# Run all tests if called directly
if __name__ == "__main__":
    test_model_results_schema()
    test_correlations_corrected_schema()
    test_non_linear_comparison_schema()
    test_permutation_results_schema()
    print("All contract tests passed.")
