"""
Contract tests for the bootstrap results schema (results/sensitivity/bootstrap_results.json).
"""
import os
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "results" / "sensitivity" / "bootstrap_results.json"

def test_bootstrap_results_exists():
    """Test that the bootstrap results file exists."""
    assert DATA_PATH.exists(), f"Bootstrap results file not found: {DATA_PATH}"

def test_bootstrap_results_structure():
    """Test that the bootstrap results have the expected structure."""
    if not DATA_PATH.exists():
        pytest.skip("Bootstrap results file not found.")
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Expected: Dict with test names as keys, containing stats like 'mean', 'ci_low', 'ci_high'
    if isinstance(data, dict):
        for key, value in data.items():
            assert isinstance(key, str), f"Key '{key}' must be a string"
            assert isinstance(value, dict), f"Value for '{key}' must be a dictionary"
            
            # Check for common bootstrap fields
            if "mean" in value:
                assert isinstance(value["mean"], (int, float))
            if "ci_low" in value:
                assert isinstance(value["ci_low"], (int, float))
            if "ci_high" in value:
                assert isinstance(value["ci_high"], (int, float))
    else:
        pytest.fail(f"Bootstrap results has unexpected type: {type(data)}")
