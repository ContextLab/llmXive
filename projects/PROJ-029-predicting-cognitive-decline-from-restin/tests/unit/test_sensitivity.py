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
    assert results[0] == results[1] # 0.45 and 0.50 might yield same result here
    # 0.6 and 0.7 are > 0.55, so they are 1. 0.5 is 0. 0.3, 0.4 are 0.
    # t=0.45: [0,0,1,1,1] -> acc: 3/5 = 0.6
    # t=0.50: [0,0,1,1,1] -> acc: 3/5 = 0.6 (0.5 >= 0.5 is True)
    # t=0.55: [0,0,0,1,1] -> acc: 4/5 = 0.8
    
    assert results[2] > results[0]
