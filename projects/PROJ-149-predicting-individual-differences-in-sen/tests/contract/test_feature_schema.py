"""
Contract tests for feature_schema and result_schema.
Validates that data files produced by the pipeline adhere to the defined schemas.
"""
import os
import sys
import json
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path to import config if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, EPSILON

# Schema definitions
FEATURE_SCHEMA = {
    "required_columns": [
        "participant_id",
        "median_rt",
        "delta_rel",
        "theta_rel",
        "alpha_rel",
        "low_beta_rel",
        "high_beta_rel",
        "gamma_rel"
    ],
    "rt_min": 100.0,
    "rt_max": 2000.0,
    "power_min": 0.0,
    "power_max": 1.0
}

MODEL_RESULTS_SCHEMA_KEYS = [
    "adjusted_r2",
    "optimal_lambda",
    "rmse",
    "test_r2",
    "test_rmse",
    "post_hoc_power_analysis"
]

CORRELATIONS_SCHEMA = {
    "required_columns": ["band", "r_value", "p_value", "n"],
    "p_value_max": 1.0
}

NON_LINEAR_SCHEMA_KEYS = [
    "linear_adj_r2",
    "nonlinear_adj_r2",
    "f_statistic",
    "p_value",
    "significant_at_0p05",
    "interpretation"
]

PERMUTATION_SCHEMA_KEYS = [
    "observed_r2",
    "p_value",
    "null_distribution_path"
]

def get_contract_path():
    """Ensure the contracts directory exists and return the path to the schema file."""
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(exist_ok=True)
    return contracts_dir / "feature_schema.schema.yaml"

def test_contract_file_exists():
    """Verify that the contract schema file exists on disk."""
    path = get_contract_path()
    assert path.exists(), f"Contract file missing: {path}"
    # Basic check that it's not empty
    assert path.stat().st_size > 0, "Contract file is empty"

def test_feature_schema_validation():
    """Validate data/processed/features.csv against the feature schema."""
    features_path = get_path("data/processed/features.csv")
    assert os.path.exists(features_path), f"Features file missing: {features_path}"
    
    df = pd.read_csv(features_path)
    
    # Check required columns
    missing_cols = set(FEATURE_SCHEMA["required_columns"]) - set(df.columns)
    assert not missing_cols, f"Missing columns in features.csv: {missing_cols}"
    
    # Check for nulls
    assert not df.isnull().any().any(), "Features file contains null values"
    
    # Check RT range
    rt_values = df["median_rt"]
    assert (rt_values >= FEATURE_SCHEMA["rt_min"]).all(), "RT values below minimum threshold"
    assert (rt_values <= FEATURE_SCHEMA["rt_max"]).all(), "RT values above maximum threshold"
    
    # Check power relative values (0 to 1)
    power_cols = [c for c in df.columns if c.endswith("_rel")]
    for col in power_cols:
        assert (df[col] >= FEATURE_SCHEMA["power_min"]).all(), f"{col} values below 0"
        assert (df[col] <= FEATURE_SCHEMA["power_max"]).all(), f"{col} values above 1"

def test_model_results_schema():
    """Validate data/processed/model_results.json keys."""
    results_path = get_path("data/processed/model_results.json")
    assert os.path.exists(results_path), f"Model results file missing: {results_path}"
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    missing_keys = set(MODEL_RESULTS_SCHEMA_KEYS) - set(data.keys())
    assert not missing_keys, f"Missing keys in model_results.json: {missing_keys}"

def test_correlations_schema():
    """Validate data/processed/correlations_corrected.csv (or raw) schema."""
    # Try corrected first, then raw if corrected doesn't exist (fallback for robustness)
    corr_path = get_path("data/processed/correlations_corrected.csv")
    if not os.path.exists(corr_path):
        corr_path = get_path("data/interim/correlations_raw.csv")
    
    assert os.path.exists(corr_path), f"Correlations file missing: {corr_path}"
    
    df = pd.read_csv(corr_path)
    missing_cols = set(CORRELATIONS_SCHEMA["required_columns"]) - set(df.columns)
    assert not missing_cols, f"Missing columns in correlations file: {missing_cols}"
    
    # Check p-value range
    assert (df["p_value"] >= 0).all(), "Negative p-values found"
    assert (df["p_value"] <= CORRELATIONS_SCHEMA["p_value_max"]).all(), "P-values > 1"

def test_non_linear_schema():
    """Validate data/processed/non_linear_comparison.json keys."""
    path = get_path("data/processed/non_linear_comparison.json")
    if not os.path.exists(path):
        # If file doesn't exist, skip test or assert failure depending on strictness
        # For contract tests, we expect the file to exist if the pipeline ran fully
        pytest.skip("Non-linear comparison file not found; pipeline may not have reached this step.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    missing_keys = set(NON_LINEAR_SCHEMA_KEYS) - set(data.keys())
    assert not missing_keys, f"Missing keys in non_linear_comparison.json: {missing_keys}"
    
    # Check boolean field
    assert isinstance(data["significant_at_0p05"], bool), "significant_at_0p05 must be boolean"

def test_permutation_schema():
    """Validate data/processed/permutation_results.json keys."""
    path = get_path("data/processed/permutation_results.json")
    if not os.path.exists(path):
        pytest.skip("Permutation results file not found; pipeline may not have reached this step.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    missing_keys = set(PERMUTATION_SCHEMA_KEYS) - set(data.keys())
    assert not missing_keys, f"Missing keys in permutation_results.json: {missing_keys}"