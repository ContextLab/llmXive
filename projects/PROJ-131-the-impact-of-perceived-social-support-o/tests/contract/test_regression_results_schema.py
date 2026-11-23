"""
Contract tests for regression results schema (T018).
Verifies that regression_results.csv contains expected columns.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

def load_results():
    results_path = Path(__file__).parent.parent.parent / "data" / "results" / "regression_results.csv"
    if not results_path.exists():
        pytest.skip("regression_results.csv not found. Run the pipeline first.")
    return pd.read_csv(results_path)

def test_regression_results_exists():
    """Test that regression results file exists."""
    results_path = Path(__file__).parent.parent.parent / "data" / "results" / "regression_results.csv"
    assert results_path.exists(), "regression_results.csv does not exist"

def test_regression_results_columns():
    """Test that regression results have required columns."""
    df = load_results()
    required_cols = ['outcome', 'coef', 'std_err', 'p_value', 'fdr_p_value', 'ci_lower', 'ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert len(missing_cols) == 0, f"Missing columns in regression results: {missing_cols}"