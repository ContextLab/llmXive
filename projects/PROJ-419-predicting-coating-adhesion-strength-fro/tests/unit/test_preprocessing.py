"""
Unit tests for preprocessing module, specifically Construct Validity Check.
"""
import pytest
import pandas as pd
import numpy as np
from preprocessing import perform_construct_validity_check


def test_valid_proxy_passes():
    """Test that a proxy with high correlation and R² is kept."""
    # Create synthetic data where proxy correlates strongly with target
    n = 100
    target = np.random.normal(0, 1, n)
    proxy_good = target * 0.8 + np.random.normal(0, 0.1, n)  # Strong correlation

    df = pd.DataFrame({
        'target': target,
        'proxy_good': proxy_good,
        'other_col': np.random.normal(0, 1, n)
    })

    valid_df, report = perform_construct_validity_check(
        df, 
        proxy_columns=['proxy_good'], 
        target_column='target',
        correlation_threshold=0.3,
        r_squared_threshold=0.05
    )

    assert 'proxy_good' in report['valid_proxies']
    assert 'proxy_good' not in report['excluded_proxies']
    assert 'proxy_good' in valid_df.columns


def test_invalid_proxy_excluded_low_corr():
    """Test that a proxy with low correlation is excluded."""
    # Create synthetic data where proxy has weak correlation
    n = 100
    target = np.random.normal(0, 1, n)
    proxy_bad = np.random.normal(0, 1, n)  # No correlation

    df = pd.DataFrame({
        'target': target,
        'proxy_bad': proxy_bad,
        'other_col': np.random.normal(0, 1, n)
    })

    valid_df, report = perform_construct_validity_check(
        df, 
        proxy_columns=['proxy_bad'], 
        target_column='target',
        correlation_threshold=0.3,
        r_squared_threshold=0.05
    )

    assert 'proxy_bad' in report['excluded_proxies']
    assert 'proxy_bad' not in valid_df.columns


def test_invalid_proxy_excluded_low_r2():
    """Test that a proxy with high correlation but low R² (if possible in noise) is excluded."""
    # In linear regression, R² is r², so if |r| is low, R² is low. 
    # We test the logic explicitly by ensuring the thresholds are respected.
    n = 100
    target = np.random.normal(0, 1, n)
    # Create a proxy that might have some correlation but we force exclusion via thresholds
    proxy_mixed = target * 0.1 + np.random.normal(0, 1, n) 

    df = pd.DataFrame({
        'target': target,
        'proxy_mixed': proxy_mixed,
        'other_col': np.random.normal(0, 1, n)
    })

    # Set high thresholds to force exclusion
    valid_df, report = perform_construct_validity_check(
        df, 
        proxy_columns=['proxy_mixed'], 
        target_column='target',
        correlation_threshold=0.9,  # Very high
        r_squared_threshold=0.5     # Very high
    )

    assert 'proxy_mixed' in report['excluded_proxies']
    assert 'proxy_mixed' not in valid_df.columns


def test_missing_target_column():
    """Test behavior when target column is missing."""
    df = pd.DataFrame({'proxy': [1, 2, 3]})
    
    valid_df, report = perform_construct_validity_check(
        df, 
        proxy_columns=['proxy'], 
        target_column='nonexistent_target'
    )

    assert report['excluded_proxies'] == ['proxy']
    assert report['valid_proxies'] == []


def test_missing_proxy_column():
    """Test behavior when proxy column is missing."""
    df = pd.DataFrame({'target': [1, 2, 3]})
    
    valid_df, report = perform_construct_validity_check(
        df, 
        proxy_columns=['missing_proxy'], 
        target_column='target'
    )

    assert report['excluded_proxies'] == ['missing_proxy']
    assert report['valid_proxies'] == []

def test_report_structure():
    """Test that the report dictionary contains expected keys."""
    df = pd.DataFrame({
        'target': [1, 2, 3, 4, 5],
        'proxy': [1, 2, 3, 4, 5]
    })
    
    _, report = perform_construct_validity_check(
        df, 
        proxy_columns=['proxy'], 
        target_column='target'
    )

    assert 'valid_proxies' in report
    assert 'excluded_proxies' in report
    assert 'metrics' in report
    assert 'thresholds' in report
    
    if report['valid_proxies']:
        proxy = report['valid_proxies'][0]
        assert 'correlation' in report['metrics'][proxy]
        assert 'r_squared' in report['metrics'][proxy]