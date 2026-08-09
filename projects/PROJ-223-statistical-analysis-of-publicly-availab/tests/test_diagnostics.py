"""
Tests for code/diagnostics.py model diagnostics and visualization.
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import sys

if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from diagnostics import (
    calculate_vif,
    sensitivity_analysis,
    plot_coefficients,
    run_diagnostics
)

# --- T025: Unit test for VIF calculation ---
def test_calculate_vif():
    """
    Test VIF calculation on a dataset with known multicollinearity.
    """
    # Create a dataset with perfect collinearity for one variable
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        'x1': np.random.rand(n),
        'x2': np.random.rand(n),
        'x3': np.random.rand(n)
    })
    # Add a perfectly collinear variable
    X['x4'] = X['x1'] * 2 + 1

    # Calculate VIF
    vif_results = calculate_vif(X)

    # Check that x4 has a very high VIF (or infinity)
    assert 'x4' in vif_results.index or 'x4' in vif_results.columns
    vif_x4 = vif_results['x4'] if 'x4' in vif_results.columns else vif_results.loc['x4', 'VIF']
    assert vif_x4 > 100  # Should be very high for perfect collinearity

    # Check that other variables have reasonable VIF
    for col in ['x1', 'x2', 'x3']:
        vif_val = vif_results[col] if 'col' in vif_results.columns else vif_results.loc[col, 'VIF']
        assert vif_val < 10  # Should be low

# --- T026: Integration test for sensitivity analysis sweep ---
def test_sensitivity_analysis():
    """
    Test that sensitivity analysis runs without error and produces expected output structure.
    """
    # Create mock data
    np.random.seed(42)
    n = 50
    data = pd.DataFrame({
        'severity': np.random.choice([0, 1, 2], n),
        'precipitation': np.random.rand(n) * 10,
        'visibility': np.random.rand(n) * 10,
        'temperature': np.random.rand(n) * 20 + 10
    })

    # Run sensitivity analysis
    # This function should sweep a parameter and report stability
    try:
        result = sensitivity_analysis(data, target_var='precipitation')
        assert isinstance(result, pd.DataFrame) or isinstance(result, dict)
        # Check for expected keys/columns like 'threshold', 'odds_ratio_change', 'stability_metric'
        # The exact structure depends on the implementation
    except Exception as e:
        pytest.fail(f"Sensitivity analysis failed: {e}")

# --- Test for coefficient plot generation ---
def test_plot_coefficients():
    """
    Test that the coefficient plot function generates a valid matplotlib figure.
    """
    # Mock coefficients data
    coeffs = pd.DataFrame({
        'variable': ['precipitation', 'visibility', 'temperature'],
        'coef': [0.5, -0.3, 0.1],
        'ci_lower': [0.4, -0.5, 0.0],
        'ci_upper': [0.6, -0.1, 0.2]
    })

    fig = plot_coefficients(coeffs)
    
    assert isinstance(fig, plt.Figure)
    plt.close(fig) # Clean up