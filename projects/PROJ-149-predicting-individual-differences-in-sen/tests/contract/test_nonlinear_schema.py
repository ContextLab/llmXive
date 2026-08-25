"""
Contract test for non_linear_comparison.json schema.
"""
import os
import json
import pytest
from pathlib import Path

# Path to the output file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "non_linear_comparison.json"

@pytest.mark.skipif(not OUTPUT_PATH.exists(), reason="Output file not generated yet")
def test_nonlinear_schema():
    """Validate the schema of non_linear_comparison.json."""
    with open(OUTPUT_PATH, 'r') as f:
        data = json.load(f)
    
    # Top-level keys
    required_keys = {"linear_model", "nonlinear_model", "f_test", "interpretation"}
    assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - set(data.keys())}"
    
    # linear_model
    lm = data["linear_model"]
    assert "r2" in lm and isinstance(lm["r2"], (int, float))
    assert "adj_r2" in lm and isinstance(lm["adj_r2"], (int, float))
    assert "rss" in lm and isinstance(lm["rss"], (int, float))
    assert "n_predictors" in lm and isinstance(lm["n_predictors"], int)
    
    # nonlinear_model
    nm = data["nonlinear_model"]
    assert "r2" in nm and isinstance(nm["r2"], (int, float))
    assert "adj_r2" in nm and isinstance(nm["adj_r2"], (int, float))
    assert "rss" in nm and isinstance(nm["rss"], (int, float))
    assert "n_predictors" in nm and isinstance(nm["n_predictors"], int)
    assert "polynomial_terms" in nm and isinstance(nm["polynomial_terms"], list)
    
    # f_test
    ft = data["f_test"]
    assert "f_statistic" in ft
    assert "p_value" in ft
    assert "significant_at_0p05" in ft and isinstance(ft["significant_at_0p05"], bool)
    assert "num_df" in ft and isinstance(ft["num_df"], int)
    assert "den_df" in ft and isinstance(ft["den_df"], int)
    
    # interpretation
    assert "interpretation" in data and isinstance(data["interpretation"], str)
    
    # Check logical consistency
    # If significant_at_0p05 is True, p_value should be < 0.05
    if ft["significant_at_0p05"]:
        assert ft["p_value"] is not None and ft["p_value"] < 0.05, "Significant but p_value >= 0.05"
    
    # Adj R2 of nonlinear should be >= linear (or very close due to float precision)
    # Actually, adding predictors can decrease adj R2 if the term is useless.
    # But it should not be drastically lower. We just check it exists.
    assert nm["adj_r2"] <= 1.0 and lm["adj_r2"] <= 1.0