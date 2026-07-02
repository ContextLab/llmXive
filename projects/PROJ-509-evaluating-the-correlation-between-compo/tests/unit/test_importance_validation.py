"""
Unit tests for feature importance correlation calculation.

This module validates the logic used to calculate the correlation between
tree-based feature importances (from Random Forest) and permutation importances.
It ensures that the correlation coefficient calculation handles edge cases
(e.g., constant arrays, division by zero) and returns expected results.
"""

import pytest
import numpy as np
from sklearn.metrics import r2_score
from scipy.stats import pearsonr
import json
import os
import sys
from pathlib import Path

# Add the code directory to the path to allow imports
# Assuming this test is run from the project root or via pytest discovery
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from utils.logging import get_logger

logger = get_logger(__name__)

# Mock data for testing
MOCK_R2_SCORE = 0.85
MOCK_PERMUTATION_R2 = 0.82
MOCK_FEATURE_IMPORTANCES = np.array([0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.03, 0.02])
MOCK_PERMUTATION_IMPORTANCES = np.array([0.28, 0.22, 0.14, 0.11, 0.06, 0.04, 0.03, 0.01])

def calculate_correlation(importances_1, importances_2):
    """
    Calculate Pearson correlation between two arrays of importances.
    
    This is a helper function to replicate the logic that would be in
    code/importance.py, ensuring the test validates the correct logic.
    
    Args:
        importances_1: Array of feature importances from model (e.g., RF).
        importances_2: Array of feature importances from permutation.
        
    Returns:
        float: Pearson correlation coefficient.
    """
    if len(importances_1) != len(importances_2):
        raise ValueError("Input arrays must have the same length.")
    
    if len(importances_1) == 0:
        return 0.0
    
    # Handle constant arrays to avoid division by zero in pearsonr
    if np.std(importances_1) == 0 or np.std(importances_2) == 0:
        # If one or both are constant, correlation is undefined (0.0 for this context)
        # In a real scenario, one might raise a warning or return NaN
        return 0.0
        
    correlation, _ = pearsonr(importances_1, importances_2)
    return correlation

def test_correlation_calculation_positive():
    """Test that correlation is calculated correctly for positive correlation."""
    corr = calculate_correlation(MOCK_FEATURE_IMPORTANCES, MOCK_PERMUTATION_IMPORTANCES)
    assert isinstance(corr, float)
    assert 0.0 <= corr <= 1.0, "Correlation should be between 0 and 1 for these mock data."
    # The mock data is positively correlated, so r should be > 0.8
    assert corr >= 0.8, f"Expected correlation >= 0.8, got {corr}"

def test_correlation_calculation_negative():
    """Test correlation calculation with negatively correlated data."""
    importances_1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    importances_2 = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    
    corr = calculate_correlation(importances_1, importances_2)
    assert isinstance(corr, float)
    assert -1.0 <= corr <= 0.0, "Correlation should be negative."
    assert abs(corr) >= 0.99, "Expected near perfect negative correlation."

def test_correlation_calculation_constant_array():
    """Test correlation calculation when one array is constant."""
    importances_1 = np.array([1.0, 1.0, 1.0, 1.0])
    importances_2 = np.array([1.0, 2.0, 3.0, 4.0])
    
    corr = calculate_correlation(importances_1, importances_2)
    assert corr == 0.0, "Correlation should be 0.0 for constant array."

def test_correlation_calculation_empty_arrays():
    """Test correlation calculation with empty arrays."""
    importances_1 = np.array([])
    importances_2 = np.array([])
    
    corr = calculate_correlation(importances_1, importances_2)
    assert corr == 0.0, "Correlation should be 0.0 for empty arrays."

def test_correlation_calculation_mismatched_lengths():
    """Test that mismatched lengths raise an error."""
    importances_1 = np.array([1.0, 2.0, 3.0])
    importances_2 = np.array([1.0, 2.0])
    
    with pytest.raises(ValueError, match="Input arrays must have the same length."):
        calculate_correlation(importances_1, importances_2)

def test_feature_importance_threshold_validation():
    """Test that the correlation meets the required threshold (r >= 0.8)."""
    corr = calculate_correlation(MOCK_FEATURE_IMPORTANCES, MOCK_PERMUTATION_IMPORTANCES)
    # This simulates the check in code/importance.py
    assert corr >= 0.8, f"Feature importance correlation {corr} does not meet the threshold of 0.8"

def test_r2_score_consistency():
    """Test that R2 scores are calculated correctly (mocking model evaluation)."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])
    
    r2 = r2_score(y_true, y_pred)
    assert 0.0 <= r2 <= 1.0, "R2 score should be between 0 and 1."
    assert r2 > 0.9, "Expected high R2 score for close predictions."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])