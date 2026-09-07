"""
Unit tests for analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from code.analysis import run_t_test, run_linear_regression, run_baseline_analysis

def test_run_t_test():
    """Test t-test calculation."""
    df = pd.DataFrame({
        'outcome': [1, 2, 3, 10, 11, 12],
        'group': ['A', 'A', 'A', 'B', 'B', 'B']
    })
    result = run_t_test(df, 'outcome', 'group')
    assert 'p_value' in result
    assert 'effect_size' in result
    assert isinstance(result['p_value'], float)

def test_run_linear_regression():
    """Test linear regression calculation."""
    df = pd.DataFrame({
        'y': [1, 2, 3, 4, 5],
        'x1': [1, 2, 3, 4, 5]
    })
    result = run_linear_regression(df, 'y', ['x1'])
    assert 'p_value' in result
    assert 'r_squared' in result
    assert isinstance(result['p_value'], float)

def test_run_baseline_analysis_auto_detect():
    """Test baseline analysis with auto-detection."""
    df = pd.DataFrame({
        'outcome': [1, 2, 3, 10, 11, 12],
        'group': ['A', 'A', 'A', 'B', 'B', 'B']
    })
    result = run_baseline_analysis(dataframe=df)
    assert result is not None
    assert 'p_value' in result
