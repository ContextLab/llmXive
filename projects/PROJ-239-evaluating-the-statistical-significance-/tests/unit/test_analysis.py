"""
Unit tests for the analysis module (T013).
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
from code.analysis import aggregate_errors


def test_aggregate_errors_basic():
    """Test basic aggregation with known rejections."""
    # Create mock results: 100 iterations, ICC=0.1, method='naive'
    # 5 rejections at alpha=0.05
    results = [
        {'p_value': 0.04, 'icc': 0.1, 'method': 'naive'} for _ in range(5)
    ] + [
        {'p_value': 0.10, 'icc': 0.1, 'method': 'naive'} for _ in range(95)
    ]
    
    alpha_levels = [0.05]
    df = aggregate_errors(results, alpha_levels)
    
    assert len(df) == 1
    assert df.iloc[0]['icc'] == 0.1
    assert df.iloc[0]['method'] == 'naive'
    assert df.iloc[0]['alpha'] == 0.05
    assert df.iloc[0]['n'] == 100
    assert df.iloc[0]['rejections'] == 5
    assert abs(df.iloc[0]['error_rate'] - 0.05) < 1e-9


def test_aggregate_errors_clopper_pearson():
    """Test that Clopper-Pearson intervals are calculated correctly."""
    # 0 rejections out of 100
    results = [{'p_value': 0.5, 'icc': 0.0, 'method': 'test'} for _ in range(100)]
    df = aggregate_errors(results, [0.05])
    
    assert df.iloc[0]['rejections'] == 0
    assert df.iloc[0]['ci_lower'] == 0.0
    # Upper bound should be small but > 0
    assert df.iloc[0]['ci_upper'] > 0.0
    
    # 100 rejections out of 100
    results = [{'p_value': 0.01, 'icc': 0.0, 'method': 'test'} for _ in range(100)]
    df = aggregate_errors(results, [0.05])
    
    assert df.iloc[0]['rejections'] == 100
    assert df.iloc[0]['ci_upper'] == 1.0
    assert df.iloc[0]['ci_lower'] < 1.0


def test_aggregate_errors_multiple_alphas():
    """Test aggregation with multiple alpha levels."""
    results = [{'p_value': 0.01, 'icc': 0.2, 'method': 'test'} for _ in range(50)] + \
              [{'p_value': 0.06, 'icc': 0.2, 'method': 'test'} for _ in range(50)]
    
    alpha_levels = [0.01, 0.05, 0.10]
    df = aggregate_errors(results, alpha_levels)
    
    assert len(df) == 3
    alphas = sorted(df['alpha'].tolist())
    assert alphas == alpha_levels


def test_aggregate_errors_empty_list():
    """Test handling of empty results list."""
    df = aggregate_errors([], [0.05])
    assert df.empty
    assert list(df.columns) == ['icc', 'method', 'alpha', 'n', 'rejections', 'error_rate', 'ci_lower', 'ci_upper']


def test_aggregate_errors_multiple_groups():
    """Test aggregation with multiple ICC/method groups."""
    results = (
        [{'p_value': 0.01, 'icc': 0.0, 'method': 'naive'} for _ in range(50)] +
        [{'p_value': 0.01, 'icc': 0.5, 'method': 'naive'} for _ in range(50)]
    )
    
    df = aggregate_errors(results, [0.05])
    
    assert len(df) == 2
    # Check that we have both ICCs
    assert 0.0 in df['icc'].values
    assert 0.5 in df['icc'].values