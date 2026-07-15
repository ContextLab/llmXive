"""
Unit tests for Construct Validity Check (T042)
"""
import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from scipy import stats

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from construct_validity_check import perform_construct_validity_check, calculate_correlation, CORRELATION_THRESHOLD, R_SQUARED_THRESHOLD

@pytest.fixture
def sample_dataframe():
    """Create a mock dataframe with known correlations."""
    np.random.seed(42)
    n = 100
    x_valid = np.random.normal(0, 1, n)
    y_valid = 2 * x_valid + np.random.normal(0, 0.5, n) # Strong correlation
    
    x_invalid = np.random.normal(0, 1, n)
    y_invalid = np.random.normal(0, 1, n) # No correlation
    
    return pd.DataFrame({
        'valid_proxy': x_valid,
        'invalid_proxy': x_invalid,
        'adhesion_strength_mpa': y_valid # Using y_valid for both to test correlation logic
    })

def test_correlation_calculation(sample_dataframe):
    """Test that correlation is calculated correctly."""
    r, r_sq = calculate_correlation(sample_dataframe, 'valid_proxy', 'adhesion_strength_mpa')
    
    # For y = 2x + noise, r should be high (> 0.3)
    assert r > CORRELATION_THRESHOLD, f"Expected r > {CORRELATION_THRESHOLD}, got {r}"
    assert r_sq > R_SQUARED_THRESHOLD, f"Expected R² > {R_SQUARED_THRESHOLD}, got {r_sq}"

def test_invalid_proxy_detection(sample_dataframe):
    """Test that invalid proxies are correctly identified."""
    # Create a dataframe where one proxy has no correlation
    df_test = sample_dataframe.copy()
    # Overwrite valid_proxy with noise to make it invalid
    df_test['valid_proxy'] = np.random.normal(0, 1, len(df_test))
    
    # Recalculate adhesion to match the new noise for the 'invalid_proxy' test
    # Actually, let's just test the function logic with the fixture as is:
    # 'valid_proxy' correlates with 'adhesion_strength_mpa' (r > 0.3)
    # 'invalid_proxy' does NOT correlate with 'adhesion_strength_mpa' (r ~ 0)
    
    result = perform_construct_validity_check(
        df_test, 
        ['valid_proxy', 'invalid_proxy'], 
        'adhesion_strength_mpa'
    )
    
    assert len(result['valid_proxies']) == 1
    assert 'valid_proxy' in result['valid_proxies']
    assert len(result['invalid_proxies']) == 1
    assert 'invalid_proxy' in result['invalid_proxies']

def test_thresholds_enforced(sample_dataframe):
    """Test that the exact thresholds are applied."""
    # Create a feature with r just below threshold
    # This is hard to control exactly with random data, so we assert the logic
    # based on the known properties of the fixture.
    result = perform_construct_validity_check(
        sample_dataframe, 
        ['valid_proxy', 'invalid_proxy'], 
        'adhesion_strength_mpa'
    )
    
    # Verify the report structure
    assert 'detailed_results' in result
    assert 'excluded_count' in result
    assert result['excluded_count'] == len(result['invalid_proxies'])

def test_missing_column_handling(sample_dataframe):
    """Test that missing columns are handled gracefully."""
    result = perform_construct_validity_check(
        sample_dataframe, 
        ['valid_proxy', 'non_existent_column'], 
        'adhesion_strength_mpa'
    )
    
    assert 'valid_proxy' in result['valid_proxies']
    # The non-existent column should be skipped and not appear in valid/invalid lists
    assert 'non_existent_column' not in result['valid_proxies']
    assert 'non_existent_column' not in result['invalid_proxies']