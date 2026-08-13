import pytest
import numpy as np
import pandas as pd
import json
import tempfile
import os

# Import from the project's models module
from models.metrics import (
    calculate_r2,
    calculate_rmse,
    calculate_mae,
    calculate_rmse_percentage_of_range,
    evaluate_model
)

def test_calculate_r2():
    """Test R² calculation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
    
    r2 = calculate_r2(y_true, y_pred)
    
    # Perfect prediction would be R² = 1.0
    # This should be close to 1.0
    assert r2 > 0.9
    assert r2 <= 1.0

def test_calculate_r2_perfect():
    """Test R² calculation with perfect predictions."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = y_true.copy()
    
    r2 = calculate_r2(y_true, y_pred)
    
    assert r2 == 1.0

def test_calculate_r2_negative():
    """Test R² calculation with poor predictions (can be negative)."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])  # Inverse relationship
    
    r2 = calculate_r2(y_true, y_pred)
    
    # R² can be negative for very poor predictions
    assert r2 < 0

def test_calculate_rmse():
    """Test RMSE calculation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
    
    rmse = calculate_rmse(y_true, y_pred)
    
    # RMSE should be positive and small for good predictions
    assert rmse > 0
    assert rmse < 0.5

def test_calculate_rmse_perfect():
    """Test RMSE with perfect predictions."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = y_true.copy()
    
    rmse = calculate_rmse(y_true, y_pred)
    
    assert rmse == 0.0

def test_calculate_mae():
    """Test MAE calculation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
    
    mae = calculate_mae(y_true, y_pred)
    
    # MAE should be positive and small for good predictions
    assert mae > 0
    assert mae < 0.5

def test_calculate_mae_perfect():
    """Test MAE with perfect predictions."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = y_true.copy()
    
    mae = calculate_mae(y_true, y_pred)
    
    assert mae == 0.0

def test_calculate_rmse_percentage_of_range():
    """Test RMSE as percentage of target range."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
    
    rmse_pct = calculate_rmse_percentage_of_range(y_true, y_pred)
    
    # Should be a percentage (0-100)
    assert 0 <= rmse_pct <= 100

def test_calculate_rmse_percentage_of_range_zero_range():
    """Test RMSE percentage with zero range (edge case)."""
    y_true = np.array([5.0, 5.0, 5.0])
    y_pred = np.array([5.0, 5.0, 5.0])
    
    # Should handle zero range gracefully
    rmse_pct = calculate_rmse_percentage_of_range(y_true, y_pred)
    assert rmse_pct == 0.0

def test_evaluate_model():
    """Test full model evaluation."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1, 4.9])
    
    metrics = evaluate_model(y_true, y_pred)
    
    # Verify all metrics are present
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mae' in metrics
    assert 'rmse_percentage_of_range' in metrics
    
    # Verify values are reasonable
    assert metrics['r2'] > 0.9
    assert metrics['rmse'] < 0.5
    assert metrics['mae'] < 0.5
    assert 0 <= metrics['rmse_percentage_of_range'] <= 100

def test_evaluate_model_multiple_targets():
    """Test evaluation with multiple target columns."""
    y_true = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0], [5.0, 50.0]])
    y_pred = np.array([[1.1, 10.5], [2.2, 20.5], [2.9, 29.5], [4.1, 40.5], [4.9, 49.5]])
    
    metrics = evaluate_model(y_true, y_pred)
    
    # Verify all metrics are present
    assert 'r2' in metrics
    assert 'rmse' in metrics
    assert 'mae' in metrics
    
    # Verify values are reasonable
    assert metrics['r2'] > 0.9
    assert metrics['rmse'] < 1.0
    assert metrics['mae'] < 1.0
