"""
Unit tests for code/utils/metrics.py
"""
import numpy as np
import pytest
from code.utils.metrics import pearson_r, r_squared, pearson_pvalue, calculate_metrics

def test_pearson_r_perfect_correlation():
    """Test Pearson r with perfect positive correlation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    r = pearson_r(y_true, y_pred)
    assert np.isclose(r, 1.0)

def test_pearson_r_perfect_negative():
    """Test Pearson r with perfect negative correlation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    r = pearson_r(y_true, y_pred)
    assert np.isclose(r, -1.0)

def test_pearson_r_no_correlation():
    """Test Pearson r with uncorrelated data."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([5.0, 1.0, 4.0, 2.0, 3.0])
    r = pearson_r(y_true, y_pred)
    # Just check it's not 1 or -1, actual value depends on specific data
    assert -1.0 < r < 1.0

def test_r_squared_perfect():
    """Test R² with perfect prediction."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    r2 = r_squared(y_true, y_pred)
    assert np.isclose(r2, 1.0)

def test_r_squared_zero():
    """Test R² with prediction equal to mean (worst case for linear model)."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0]) # Mean of y_true
    r2 = r_squared(y_true, y_pred)
    assert np.isclose(r2, 0.0)

def test_r_squared_negative():
    """Test R² with worse than mean prediction."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0]) # Inverse, high error
    r2 = r_squared(y_true, y_pred)
    # SS_res will be large, SS_tot is fixed. 
    # SS_res = sum((y - y)^2) = 0? No, y_pred is inverse.
    # y_true: 1,2,3,4,5. y_pred: 5,4,3,2,1.
    # Residuals: -4, -2, 0, 2, 4. Sq: 16, 4, 0, 4, 16. Sum = 40.
    # SS_tot: mean=3. Devs: -2, -1, 0, 1, 2. Sq: 4, 1, 0, 1, 4. Sum = 10.
    # R2 = 1 - 40/10 = -3.
    assert r2 < 0.0

def test_metrics_dict():
    """Test that calculate_metrics returns a dictionary with correct keys."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
    metrics = calculate_metrics(y_true, y_pred)
    
    assert "pearson_r" in metrics
    assert "r_squared" in metrics
    assert "p_value" in metrics
    
    assert isinstance(metrics["pearson_r"], float)
    assert isinstance(metrics["r_squared"], float)
    assert isinstance(metrics["p_value"], float)

def test_empty_input():
    """Test that empty inputs raise ValueError."""
    with pytest.raises(ValueError):
        pearson_r([], [])
    
    with pytest.raises(ValueError):
        r_squared([], [])

def test_mismatched_shapes():
    """Test that mismatched shapes raise ValueError."""
    with pytest.raises(ValueError):
        pearson_r([1, 2, 3], [1, 2])