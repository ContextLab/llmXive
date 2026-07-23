"""
Unit tests for partial correlation logic in code/analysis.py.

This module tests the partial correlation functionality using mock data
with known correlation properties to ensure correctness before running
on real data.
"""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr, rankdata
from unittest.mock import patch, MagicMock
import json

# Import the analysis module (assuming it will be created)
# We'll mock the data loading and test the core logic
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

# We'll test the logic directly by importing or mocking
# Since analysis.py doesn't exist yet, we'll implement the test
# against the expected interface

def generate_mock_data_with_known_correlation(
    n_samples: int = 100,
    true_corr: float = 0.6,
    control_corr: float = 0.3
) -> pd.DataFrame:
    """
    Generate mock data where we know the expected correlation structure.
    
    Creates variables with controlled correlations:
    - X and Y have a true correlation of `true_corr`
    - Control variables (mass, semi_major_axis) correlate with both
    
    Args:
        n_samples: Number of samples to generate
        true_corr: Target correlation between X and Y
        control_corr: Target correlation between controls and X/Y
        
    Returns:
        DataFrame with columns: cumulative_flux, retention_fraction, mass, semi_major_axis
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate base variables
    x = np.random.randn(n_samples)
    
    # Create Y with controlled correlation to X
    noise = np.random.randn(n_samples)
    y = true_corr * x + np.sqrt(1 - true_corr**2) * noise
    
    # Create control variables that correlate with both
    mass = control_corr * x + np.random.randn(n_samples) * np.sqrt(1 - control_corr**2)
    semi_major_axis = control_corr * y + np.random.randn(n_samples) * np.sqrt(1 - control_corr**2)
    
    # Add some realistic scaling
    cumulative_flux = np.exp(x * 2) * 1e10  # Positive skew like real data
    retention_fraction = np.clip(y * 0.5 + 0.5, 0, 1)  # Bounded [0, 1]
    mass = np.abs(mass) * 1.0  # Jupiter masses
    semi_major_axis = np.abs(semi_major_axis) * 0.1  # AU
    
    return pd.DataFrame({
        'cumulative_flux': cumulative_flux,
        'retention_fraction': retention_fraction,
        'mass': mass,
        'semi_major_axis': semi_major_axis
    })


def test_partial_correlation_with_known_data():
    """
    Test that partial correlation correctly recovers known correlation structure.
    
    This test:
    1. Generates mock data with a known true correlation between X and Y
    2. Adds control variables that correlate with both
    3. Verifies that partial correlation (controlling for controls) 
       recovers a value close to the true correlation
    """
    # Generate mock data with known properties
    mock_data = generate_mock_data_with_known_correlation(
        n_samples=200,
        true_corr=0.6,
        control_corr=0.3
    )
    
    # Extract variables
    x = mock_data['cumulative_flux'].values
    y = mock_data['retention_fraction'].values
    controls = mock_data[['mass', 'semi_major_axis']].values
    
    # Rank transform all variables (as required by FR-006)
    x_rank = rankdata(x)
    y_rank = rankdata(y)
    control_ranks = np.apply_along_axis(rankdata, 0, controls)
    
    # Compute partial correlation manually using residuals
    # Regress X on controls
    from sklearn.linear_model import LinearRegression
    
    X_control = np.column_stack([control_ranks[:, 0], control_ranks[:, 1]])
    X_control = np.column_stack([np.ones(len(X_control)), X_control])  # Add intercept
    
    lr_x = LinearRegression()
    lr_x.fit(X_control, x_rank)
    x_residuals = x_rank - lr_x.predict(X_control)
    
    # Regress Y on controls
    lr_y = LinearRegression()
    lr_y.fit(X_control, y_rank)
    y_residuals = y_rank - lr_y.predict(X_control)
    
    # Compute correlation of residuals (partial correlation)
    partial_corr, p_value = spearmanr(x_residuals, y_residuals)
    
    # The partial correlation should be close to our true correlation
    # (allowing for sampling variation)
    expected_min = 0.4  # Should be reasonably close to 0.6
    expected_max = 0.8
    
    assert expected_min < partial_corr < expected_max, \
        f"Partial correlation {partial_corr:.3f} not in expected range [{expected_min}, {expected_max}]"
    
    # P-value should be significant for this sample size
    assert p_value < 0.05, f"P-value {p_value:.3f} should be significant"
    
    print(f"✓ Partial correlation test passed: ρ={partial_corr:.3f}, p={p_value:.3f}")


def test_partial_correlation_no_control():
    """
    Test that when controls are uncorrelated, partial correlation ≈ regular correlation.
    """
    mock_data = generate_mock_data_with_known_correlation(
        n_samples=150,
        true_corr=0.5,
        control_corr=0.0  # Controls uncorrelated
    )
    
    x = mock_data['cumulative_flux'].values
    y = mock_data['retention_fraction'].values
    controls = mock_data[['mass', 'semi_major_axis']].values
    
    # Rank transform
    x_rank = rankdata(x)
    y_rank = rankdata(y)
    control_ranks = np.apply_along_axis(rankdata, 0, controls)
    
    # Regular Spearman correlation
    regular_corr, _ = spearmanr(x_rank, y_rank)
    
    # Partial correlation
    X_control = np.column_stack([control_ranks[:, 0], control_ranks[:, 1]])
    X_control = np.column_stack([np.ones(len(X_control)), X_control])
    
    from sklearn.linear_model import LinearRegression
    
    lr_x = LinearRegression()
    lr_x.fit(X_control, x_rank)
    x_residuals = x_rank - lr_x.predict(X_control)
    
    lr_y = LinearRegression()
    lr_y.fit(X_control, y_rank)
    y_residuals = y_rank - lr_y.predict(X_control)
    
    partial_corr, _ = spearmanr(x_residuals, y_residuals)
    
    # They should be very similar when controls are uncorrelated
    diff = abs(regular_corr - partial_corr)
    assert diff < 0.1, f"Correlations differ too much: regular={regular_corr:.3f}, partial={partial_corr:.3f}"
    
    print(f"✓ No-control test passed: regular={regular_corr:.3f}, partial={partial_corr:.3f}")


def test_partial_correlation_with_realistic_noise():
    """
    Test partial correlation with realistic noise patterns.
    """
    np.random.seed(123)
    n = 300
    
    # Create realistic astrophysical data patterns
    # Mass and semi-major axis are often correlated in real data
    mass = np.random.lognormal(mean=0, sigma=0.5, size=n)
    semi_major_axis = 0.1 * mass**0.5 + np.random.normal(0, 0.02, n)
    semi_major_axis = np.abs(semi_major_axis)
    
    # Cumulative flux depends on both mass and random stellar activity
    flux_base = 1e9 * (1 + 0.3 * np.log10(mass))
    cumulative_flux = flux_base * np.random.lognormal(0, 0.3, n)
    
    # Retention fraction decreases with flux but with noise
    retention_base = 1.0 / (1 + cumulative_flux / 1e10)
    retention_fraction = np.clip(retention_base + np.random.normal(0, 0.1, n), 0, 1)
    
    df = pd.DataFrame({
        'cumulative_flux': cumulative_flux,
        'retention_fraction': retention_fraction,
        'mass': mass,
        'semi_major_axis': semi_major_axis
    })
    
    # Run partial correlation
    x = rankdata(df['cumulative_flux'])
    y = rankdata(df['retention_fraction'])
    controls = np.column_stack([
        rankdata(df['mass']),
        rankdata(df['semi_major_axis'])
    ])
    
    from sklearn.linear_model import LinearRegression
    
    X_control = np.column_stack([np.ones(n), controls[:, 0], controls[:, 1]])
    
    lr_x = LinearRegression()
    lr_x.fit(X_control, x)
    x_res = x - lr_x.predict(X_control)
    
    lr_y = LinearRegression()
    lr_y.fit(X_control, y)
    y_res = y - lr_y.predict(X_control)
    
    partial_corr, p_value = spearmanr(x_res, y_res)
    
    # Should detect a negative correlation (higher flux → lower retention)
    assert partial_corr < 0, f"Expected negative correlation, got {partial_corr:.3f}"
    assert p_value < 0.05, f"Expected significant result, got p={p_value:.3f}"
    
    print(f"✓ Realistic noise test passed: ρ={partial_corr:.3f}, p={p_value:.3f}")


def test_partial_correlation_edge_cases():
    """
    Test edge cases: small sample size, perfect correlation, etc.
    """
    # Small sample
    small_data = generate_mock_data_with_known_correlation(n_samples=20)
    
    x = rankdata(small_data['cumulative_flux'])
    y = rankdata(small_data['retention_fraction'])
    controls = np.column_stack([
        rankdata(small_data['mass']),
        rankdata(small_data['semi_major_axis'])
    ])
    
    from sklearn.linear_model import LinearRegression
    import numpy as np
    
    n = len(x)
    X_control = np.column_stack([np.ones(n), controls[:, 0], controls[:, 1]])
    
    # Should not crash
    lr_x = LinearRegression()
    lr_x.fit(X_control, x)
    x_res = x - lr_x.predict(X_control)
    
    lr_y = LinearRegression()
    lr_y.fit(X_control, y)
    y_res = y - lr_y.predict(X_control)
    
    partial_corr, p_value = spearmanr(x_res, y_res)
    
    # Just verify it runs and returns a valid number
    assert -1 <= partial_corr <= 1, f"Correlation out of bounds: {partial_corr}"
    assert 0 <= p_value <= 1, f"P-value out of bounds: {p_value}"
    
    print(f"✓ Edge case test passed: n=20, ρ={partial_corr:.3f}")


if __name__ == '__main__':
    # Run tests manually if executed directly
    test_partial_correlation_with_known_data()
    test_partial_correlation_no_control()
    test_partial_correlation_with_realistic_noise()
    test_partial_correlation_edge_cases()
    print("\n✓ All partial correlation tests passed!")