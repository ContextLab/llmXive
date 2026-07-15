"""
Unit tests for the merge_results script logic.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from scripts.merge_results import (
    load_results,
    prepare_baseline_for_aggregation,
    prepare_robust_for_aggregation,
    compute_error_rates_and_ci
)

def test_load_results_missing_file():
    """Test that load_results raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_results('nonexistent_file.csv')

def test_load_results_empty_file(tmp_path):
    """Test that load_results raises ValueError for empty file."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    with pytest.raises(ValueError):
        load_results(str(empty_file))

def test_load_results_valid(tmp_path):
    """Test loading a valid results file."""
    valid_file = tmp_path / "valid.csv"
    valid_file.write_text("iteration,icc,p_value,rejected\n0,0.1,0.03,True\n1,0.1,0.06,False\n")
    df = load_results(str(valid_file))
    assert len(df) == 2
    assert 'p_value' in df.columns
    assert 'icc' in df.columns

def test_prepare_baseline_for_aggregation():
    """Test that baseline prep adds 'method' column."""
    df = pd.DataFrame({
        'iteration': [0, 1],
        'icc': [0.1, 0.1],
        'p_value': [0.03, 0.06],
        'rejected': [True, False]
    })
    result = prepare_baseline_for_aggregation(df)
    assert 'method' in result.columns
    assert all(result['method'] == 'naive')

def test_prepare_robust_for_aggregation():
    """Test that robust prep handles boolean conversion."""
    df = pd.DataFrame({
        'iteration': [0, 1],
        'icc': [0.1, 0.1],
        'method': ['robust', 'robust'],
        'p_value': [0.03, 0.06],
        'rejected': ['True', 'False']  # String representation
    })
    result = prepare_robust_for_aggregation(df)
    assert result['rejected'].dtype == bool
    assert result['rejected'].iloc[0] == True
    assert result['rejected'].iloc[1] == False

def test_compute_error_rates_and_ci():
    """Test error rate and CI computation."""
    # Create synthetic data where we know the expected outcome
    # 10 iterations, ICC=0.1, Method=naive
    # 5 rejections at alpha=0.05 -> error rate = 0.5
    df = pd.DataFrame({
        'icc': [0.1] * 10,
        'method': ['naive'] * 10,
        'p_value': [0.04] * 5 + [0.06] * 5,  # 5 < 0.05, 5 >= 0.05
        'rejected': [True] * 5 + [False] * 5
    })

    alpha_levels = [0.05]
    result_df = compute_error_rates_and_ci(df, alpha_levels)

    assert len(result_df) == 1
    row = result_df.iloc[0]
    assert row['ICC'] == 0.1
    assert row['Alpha'] == 0.05
    assert row['Method'] == 'naive'
    assert row['Empirical_Error_Rate'] == 0.5
    # CI should be non-zero and less than 1
    assert 0.0 < row['CI_Lower'] < row['CI_Upper'] < 1.0

def test_compute_error_rates_multiple_alphas():
    """Test computation across multiple alpha levels."""
    df = pd.DataFrame({
        'icc': [0.1] * 10,
        'method': ['naive'] * 10,
        'p_value': [0.01, 0.02, 0.04, 0.06, 0.08, 0.09, 0.10, 0.20, 0.50, 0.90],
        'rejected': [True, True, True, False, False, False, False, False, False, False]
    })

    alpha_levels = [0.05, 0.10]
    result_df = compute_error_rates_and_ci(df, alpha_levels)

    assert len(result_df) == 2

    # Check alpha=0.05 (3 rejections: 0.01, 0.02, 0.04)
    row_05 = result_df[result_df['Alpha'] == 0.05].iloc[0]
    assert row_05['Empirical_Error_Rate'] == 0.3

    # Check alpha=0.10 (6 rejections: 0.01, 0.02, 0.04, 0.06, 0.08, 0.09)
    row_10 = result_df[result_df['Alpha'] == 0.10].iloc[0]
    assert row_10['Empirical_Error_Rate'] == 0.6
