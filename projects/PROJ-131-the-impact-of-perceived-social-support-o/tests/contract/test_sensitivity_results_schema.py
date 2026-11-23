"""
Contract tests for sensitivity results schema (T026).
Verifies that sensitivity_analysis.csv and coefficient_comparison.csv have expected columns.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

def load_sensitivity():
    path = Path(__file__).parent.parent.parent / "data" / "results" / "sensitivity_analysis.csv"
    if not path.exists():
        pytest.skip("sensitivity_analysis.csv not found.")
    return pd.read_csv(path)

def load_comparison():
    path = Path(__file__).parent.parent.parent / "data" / "results" / "coefficient_comparison.csv"
    if not path.exists():
        pytest.skip("coefficient_comparison.csv not found.")
    return pd.read_csv(path)

def test_sensitivity_results_columns():
    """Test sensitivity analysis columns."""
    df = load_sensitivity()
    required = ['scenario', 'outcome', 'coef', 'std_err', 'p_value']
    missing = [c for c in required if c not in df.columns]
    assert len(missing) == 0, f"Missing columns: {missing}"

def test_coefficient_comparison_columns():
    """Test coefficient comparison columns."""
    df = load_comparison()
    required = ['scenario', 'outcome', 'baseline_coef', 'sensitivity_coef', 'shift']
    missing = [c for c in required if c not in df.columns]
    assert len(missing) == 0, f"Missing columns: {missing}"