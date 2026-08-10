"""
Unit tests for sensitivity_analysis.py
"""

import pytest
import numpy as np
import pandas as pd
import json
import tempfile
from pathlib import Path
from scripts.sensitivity_analysis import (
    sweep_thresholds,
    find_optimal_threshold,
    run_analysis
)

def test_sweep_thresholds_basic():
    """Test basic threshold sweeping logic."""
    # Simple case: 10 samples, 5 anomalies
    scores = np.array([0.1, 0.2, 0.3, 0.8, 0.9, 0.1, 0.2, 0.3, 0.8, 0.9])
    labels = np.array([0, 0, 0, 1, 1, 0, 0, 0, 1, 1])
    thresholds = np.array([0.0, 0.5, 1.0])

    results = sweep_thresholds(scores, labels, thresholds)

    assert len(results) == 3

    # At threshold 0.0: all predicted 1
    # TP=4, FP=6, TN=0, FN=0 -> Sensitivity=1.0, Specificity=0.0
    res_0 = results[0]
    assert res_0['threshold'] == 0.0
    assert res_0['sensitivity'] == 1.0
    assert res_0['specificity'] == 0.0
    assert res_0['true_positives'] == 4
    assert res_0['false_positives'] == 6

    # At threshold 1.0: all predicted 0
    # TP=0, FP=0, TN=6, FN=4 -> Sensitivity=0.0, Specificity=1.0
    res_1 = results[2]
    assert res_1['threshold'] == 1.0
    assert res_1['sensitivity'] == 0.0
    assert res_1['specificity'] == 1.0
    assert res_1['false_negatives'] == 4

def test_find_optimal_threshold_f1():
    """Test finding the F1 optimal threshold."""
    results = [
        {"threshold": 0.1, "f1_score": 0.5},
        {"threshold": 0.5, "f1_score": 0.8},
        {"threshold": 0.9, "f1_score": 0.3}
    ]

    optimal = find_optimal_threshold(results, target="f1")
    assert optimal['threshold'] == 0.5
    assert optimal['f1_score'] == 0.8

def test_run_analysis_integration():
    """Test the full run_analysis function with temporary files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create dummy predictions
        pred_data = {
            "score": [0.1, 0.4, 0.6, 0.9]
        }
        pred_df = pd.DataFrame(pred_data)
        pred_file = tmp_path / "preds.csv"
        pred_df.to_csv(pred_file, index=False)

        # Create dummy ground truth
        gt_data = {
            "anomaly_flag": [0, 0, 1, 1]
        }
        gt_df = pd.DataFrame(gt_data)
        gt_file = tmp_path / "gt.csv"
        gt_df.to_csv(gt_file, index=False)

        output_file = tmp_path / "results.json"

        # Run analysis
        results = run_analysis(pred_file, gt_file, output_file)

        # Verify output file exists
        assert output_file.exists()

        # Verify structure
        assert "metadata" in results
        assert "global_metrics" in results
        assert "optimal_thresholds" in results
        assert "threshold_sweep" in results

        # Verify AUC is calculated (should be 1.0 for perfect separation here)
        assert results["global_metrics"]["auc_roc"] >= 0.5

def test_edge_cases():
    """Test edge cases like all negative or all positive labels."""
    # All negative
    scores = np.array([0.1, 0.2, 0.3])
    labels = np.array([0, 0, 0])
    thresholds = np.array([0.5])
    
    results = sweep_thresholds(scores, labels, thresholds)
    # At 0.5, all predicted 0 -> TP=0, FP=0, TN=3, FN=0
    # Sensitivity is 0/0 -> 0.0 (handled in function)
    # Specificity is 3/3 -> 1.0
    assert results[0]['specificity'] == 1.0
    assert results[0]['sensitivity'] == 0.0