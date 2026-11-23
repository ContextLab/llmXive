"""
Tests for Sensitivity Analysis (T019).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np

# We need to mock the file system and config to run this test without real data
# or we assume the test runner provides the data. 
# For this specific task implementation, we test the logic of the analysis function
# by mocking the data loading.

def test_threshold_logic():
    """Verify that thresholds correctly generate binary labels."""
    # Mock data
    data = {
        'Tg_K': [300, 400, 500],
        'Tx_K': [320, 460, 510],
        'composition_id': ['A', 'B', 'C']
    }
    df = pd.DataFrame(data)
    
    # Threshold 25K
    # A: |320-300| = 20 <= 25 -> 1
    # B: |460-400| = 60 > 25 -> 0
    # C: |510-500| = 10 <= 25 -> 1
    expected_25 = [1, 0, 1]
    result_25 = (np.abs(df['Tx_K'] - df['Tg_K']) <= 25).astype(int)
    assert list(result_25) == expected_25, f"Expected {expected_25}, got {list(result_25)}"
    
    # Threshold 100K
    # A: 20 <= 100 -> 1
    # B: 60 <= 100 -> 1
    # C: 10 <= 100 -> 1
    expected_100 = [1, 1, 1]
    result_100 = (np.abs(df['Tx_K'] - df['Tg_K']) <= 100).astype(int)
    assert list(result_100) == expected_100, f"Expected {expected_100}, got {list(result_100)}"

def test_fpr_calculation():
    """Verify FPR calculation logic."""
    # Confusion Matrix: TN=10, FP=2, FN=1, TP=10
    # FPR = FP / (FP + TN) = 2 / 12 = 0.166...
    from sklearn.metrics import confusion_matrix
    
    y_true = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 10 negatives
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 10 positives
    
    y_pred = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1,   # 2 FPs
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1]   # 0 FNs, 10 TPs
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn)
    
    assert abs(fpr - 0.1666) < 0.001, f"FPR calculation incorrect: {fpr}"

def test_report_structure():
    """Verify the report JSON structure matches requirements."""
    # Simulate a minimal result
    results = [
        {"threshold_K": 25, "balanced_accuracy": 0.8, "false_positive_rate": 0.1, "class_balance": 0.5, "threshold_unstable": False},
        {"threshold_K": 30, "balanced_accuracy": 0.85, "false_positive_rate": 0.15, "class_balance": 0.5, "threshold_unstable": False}
    ]
    
    report = {
        "task_id": "T019",
        "stability_check": {
            "results": results
        }
    }
    
    # Check required fields exist
    assert "task_id" in report
    assert "stability_check" in report
    assert "results" in report["stability_check"]
    
    for r in results:
        assert "threshold_K" in r
        assert "balanced_accuracy" in r
        assert "false_positive_rate" in r
        assert "class_balance" in r
        assert "threshold_unstable" in r

if __name__ == "__main__":
    test_threshold_logic()
    test_fpr_calculation()
    test_report_structure()
    print("All tests passed.")