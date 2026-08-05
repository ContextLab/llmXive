"""
Unit tests for Variance Inflation Factor (VIF) calculation correctness.

This module verifies the VIF calculation logic used in code/03_model.py.
It tests both the statistical correctness against known values and edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.utils import log_setup

# Setup logging for test output
logger = log_setup()

def calculate_vif(df, features):
    """
    Helper function to calculate VIF for a set of features.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the features
    features : list
        List of column names to calculate VIF for
        
    Returns:
    --------
    dict
        Dictionary mapping feature names to their VIF values
    """
    # Add constant for intercept
    X = add_constant(df[features])
    
    vif_data = {}
    for i, feature in enumerate(features):
        # Calculate VIF for each feature
        vif = variance_inflation_factor(X.values, i + 1)  # +1 because index 0 is the constant
        vif_data[feature] = vif
        
    return vif_data

def test_vif_perfect_collinearity():
    """
    Test VIF calculation with perfect collinearity.
    
    When two variables are perfectly correlated, VIF should be infinite (or very large).
    """
    logger.info("Testing VIF with perfect collinearity...")
    
    # Create data with perfect collinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = x1 * 2  # Perfectly correlated
    x3 = np.random.randn(n)  # Independent
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    vif_results = calculate_vif(df, ['x1', 'x2', 'x3'])
    
    # x1 and x2 should have very high VIF (> 1000)
    assert vif_results['x1'] > 1000, f"Expected very high VIF for x1, got {vif_results['x1']}"
    assert vif_results['x2'] > 1000, f"Expected very high VIF for x2, got {vif_results['x2']}"
    
    # x3 should have VIF close to 1
    assert 0.9 < vif_results['x3'] < 1.1, f"Expected VIF close to 1 for x3, got {vif_results['x3']}"
    
    logger.info("✓ Perfect collinearity test passed")

def test_vif_no_collinearity():
    """
    Test VIF calculation with independent variables.
    
    When variables are independent, VIF should be close to 1.
    """
    logger.info("Testing VIF with independent variables...")
    
    # Create data with independent variables
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = np.random.randn(n)
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    vif_results = calculate_vif(df, ['x1', 'x2', 'x3'])
    
    # All VIFs should be close to 1
    for feature, vif in vif_results.items():
        assert 0.9 < vif < 1.1, f"Expected VIF close to 1 for {feature}, got {vif}"
    
    logger.info("✓ Independent variables test passed")

def test_vif_known_values():
    """
    Test VIF calculation against known values.
    
    Uses a small dataset with known correlation structure.
    """
    logger.info("Testing VIF against known values...")
    
    # Create a simple dataset with known correlations
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [2, 4, 6, 8, 10],  # Perfectly correlated with A
        'C': [1, 3, 2, 4, 3]   # Moderately correlated
    })
    
    vif_results = calculate_vif(df, ['A', 'B', 'C'])
    
    # A and B should have very high VIF
    assert vif_results['A'] > 100, f"Expected high VIF for A, got {vif_results['A']}"
    assert vif_results['B'] > 100, f"Expected high VIF for B, got {vif_results['B']}"
    
    # C should have moderate VIF
    assert vif_results['C'] > 1, f"Expected VIF > 1 for C, got {vif_results['C']}"
    
    logger.info("✓ Known values test passed")

def test_vif_single_variable():
    """
    Test VIF calculation with a single variable.
    
    A single variable should have VIF = 1.
    """
    logger.info("Testing VIF with single variable...")
    
    np.random.seed(42)
    n = 50
    x1 = np.random.randn(n)
    
    df = pd.DataFrame({'x1': x1})
    
    vif_results = calculate_vif(df, ['x1'])
    
    assert abs(vif_results['x1'] - 1.0) < 0.01, f"Expected VIF = 1 for single variable, got {vif_results['x1']}"
    
    logger.info("✓ Single variable test passed")

def test_vif_with_interaction_terms():
    """
    Test VIF calculation with interaction terms.
    
    Interaction terms often have high VIF due to correlation with main effects.
    """
    logger.info("Testing VIF with interaction terms...")
    
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = np.random.randn(n)
    interaction = x1 * x2
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'interaction': interaction
    })
    
    vif_results = calculate_vif(df, ['x1', 'x2', 'interaction'])
    
    # Interaction term typically has higher VIF
    assert vif_results['interaction'] > 1, f"Expected VIF > 1 for interaction term, got {vif_results['interaction']}"
    
    # Main effects should have VIF >= 1
    assert vif_results['x1'] >= 1, f"Expected VIF >= 1 for x1, got {vif_results['x1']}"
    assert vif_results['x2'] >= 1, f"Expected VIF >= 1 for x2, got {vif_results['x2']}"
    
    logger.info("✓ Interaction terms test passed")

def test_vif_threshold_check():
    """
    Test VIF threshold checking logic.
    
    Verify that VIF values above a threshold (e.g., 5 or 10) are correctly identified.
    """
    logger.info("Testing VIF threshold check...")
    
    # Create data with moderate collinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.randn(n)
    x2 = x1 * 0.8 + np.random.randn(n) * 0.2  # High correlation but not perfect
    x3 = np.random.randn(n)
    
    df = pd.DataFrame({
        'x1': x1,
        'x2': x2,
        'x3': x3
    })
    
    vif_results = calculate_vif(df, ['x1', 'x2', 'x3'])
    
    # x1 and x2 should have VIF > 5 (moderate collinearity)
    assert vif_results['x1'] > 5, f"Expected VIF > 5 for x1, got {vif_results['x1']}"
    assert vif_results['x2'] > 5, f"Expected VIF > 5 for x2, got {vif_results['x2']}"
    
    # x3 should have VIF close to 1
    assert vif_results['x3'] < 2, f"Expected VIF < 2 for x3, got {vif_results['x3']}"
    
    logger.info("✓ Threshold check test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])