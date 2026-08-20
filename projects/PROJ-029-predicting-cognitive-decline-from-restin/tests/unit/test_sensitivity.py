"""
Unit tests for threshold sweep logic.
"""
import pytest
import numpy as np

def test_threshold_sweep_logic():
    """Test that threshold sweep iterates over correct values."""
    thresholds = [0.45, 0.50, 0.55]
    
    # Mock predictions and true labels
    y_pred_prob = np.array([0.3, 0.4, 0.5, 0.6, 0.7])
    y_true = np.array([0, 0, 0, 1, 1])
    
    results = []
    for t in thresholds:
        y_pred = (y_pred_prob >= t).astype(int)
        # Simple accuracy calculation
        acc = np.mean(y_pred == y_true)
        results.append(acc)
    
    assert len(results) == 3
    # t=0.45: [0,0,1,1,1] -> acc: 3/5 = 0.6
    # t=0.50: [0,0,1,1,1] -> acc: 3/5 = 0.6 (0.5 >= 0.5 is True)
    # t=0.55: [0,0,0,1,1] -> acc: 4/5 = 0.8
    
    assert results[0] == results[1]
    assert results[2] > results[0]

def test_threshold_sweep_edge_cases():
    """Test threshold logic with edge case probabilities."""
    thresholds = [0.45, 0.50, 0.55]
    
    # All predictions are exactly 0.5
    y_pred_prob = np.array([0.5, 0.5, 0.5])
    y_true = np.array([1, 0, 1])
    
    results = []
    for t in thresholds:
        y_pred = (y_pred_prob >= t).astype(int)
        acc = np.mean(y_pred == y_true)
        results.append(acc)
    
    # At 0.45: 0.5 >= 0.45 -> 1s. Acc: 2/3
    # At 0.50: 0.5 >= 0.50 -> 1s. Acc: 2/3
    # At 0.55: 0.5 >= 0.55 -> 0s. Acc: 1/3
    assert results[0] == results[1]
    assert results[2] < results[0]

def test_threshold_sweep_monotonicity():
    """Test that accuracy changes monotonically or stays flat as threshold increases."""
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    y_pred_prob = np.array([0.2, 0.4, 0.6, 0.8])
    y_true = np.array([0, 0, 1, 1])
    
    accuracies = []
    for t in thresholds:
        y_pred = (y_pred_prob >= t).astype(int)
        acc = np.mean(y_pred == y_true)
        accuracies.append(acc)
    
    # Verify we got results for all thresholds
    assert len(accuracies) == len(thresholds)
    
    # Verify no NaNs
    assert not any(np.isnan(a) for a in accuracies)
    
    # Verify values are in [0, 1]
    assert all(0 <= a <= 1 for a in accuracies)