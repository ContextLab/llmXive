"""
Unit tests for aggregate_metrics.py (Task T024).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.aggregate_metrics import calculate_aggregations, load_predictions, save_results

def test_calculate_aggregations_logistic_regression():
    """Test aggregation logic for Logistic Regression."""
    # Mock data: 10 repeats, 5 folds each
    mock_predictions = {
        "logistic_regression": {
            "fold_predictions": []
        },
        "random_forest": {
            "fold_predictions": []
        }
    }

    # Generate synthetic but structured data for testing
    # We want to verify the math: mean of means
    lr_roc_values = []
    for r in range(10):
        for f in range(5):
            # Create a predictable value: 0.7 + r * 0.01 + f * 0.001
            val = 0.7 + (r * 0.01) + (f * 0.001)
            mock_predictions["logistic_regression"]["fold_predictions"].append({
                "repeat": r,
                "fold": f,
                "roc_auc": val,
                "f1": val * 0.9
            })
            lr_roc_values.append(val)

    # Calculate expected mean and std manually
    # Mean per repeat
    repeat_means = []
    for r in range(10):
        vals = [v for v in lr_roc_values if v >= 0.7 + r * 0.01 and v < 0.7 + (r + 1) * 0.01]
        # Actually, let's just slice correctly based on the generation logic
        # r=0: 0.700, 0.701, 0.702, 0.703, 0.704 -> mean 0.702
        # r=1: 0.710, 0.711, ... -> mean 0.712
        # ...
        # r=9: 0.790 ... 0.794 -> mean 0.792
        # Grand mean of [0.702, 0.712, ..., 0.792]
        pass 

    # Re-calculate expected values precisely
    expected_repeat_means = []
    expected_f1_means = []
    
    for r in range(10):
        roc_vals = [0.7 + (r * 0.01) + (f * 0.001) for f in range(5)]
        f1_vals = [v * 0.9 for v in roc_vals]
        expected_repeat_means.append(np.mean(roc_vals))
        expected_f1_means.append(np.mean(f1_vals))
    
    expected_grand_mean_roc = float(np.mean(expected_repeat_means))
    expected_grand_std_roc = float(np.std(expected_repeat_means, ddof=1))
    expected_grand_mean_f1 = float(np.mean(expected_f1_means))
    expected_grand_std_f1 = float(np.std(expected_f1_means, ddof=1))

    results = calculate_aggregations(mock_predictions)

    assert "logistic_regression" in results
    assert "random_forest" in results
    
    # Check Logistic Regression
    assert np.isclose(results["logistic_regression"]["mean_roc_auc"], expected_grand_mean_roc, atol=1e-5)
    assert np.isclose(results["logistic_regression"]["std_roc_auc"], expected_grand_std_roc, atol=1e-5)
    assert np.isclose(results["logistic_regression"]["mean_f1"], expected_grand_mean_f1, atol=1e-5)
    assert np.isclose(results["logistic_regression"]["std_f1"], expected_grand_std_f1, atol=1e-5)

def test_calculate_aggregations_empty_data():
    """Test handling of empty predictions."""
    mock_predictions = {
        "logistic_regression": {
            "fold_predictions": []
        }
    }
    results = calculate_aggregations(mock_predictions)
    assert "logistic_regression" not in results

def test_calculate_aggregations_missing_fields():
    """Test handling of entries missing repeat/fold."""
    mock_predictions = {
        "logistic_regression": {
            "fold_predictions": [
                {"repeat": 0, "fold": 0, "roc_auc": 0.8},
                {"fold": 0, "roc_auc": 0.9}, # Missing repeat
                {"repeat": 1, "roc_auc": 0.85} # Missing fold
            ]
        }
    }
    # Should log warnings and skip invalid entries, not crash
    results = calculate_aggregations(mock_predictions)
    # Only the first valid entry should be counted (though 1 entry is not enough for std)
    # The logic handles single repeat by setting std=0.0 if len < 2
    assert "logistic_regression" in results
    assert results["logistic_regression"]["mean_roc_auc"] == 0.8
    assert results["logistic_regression"]["std_roc_auc"] == 0.0

def test_save_results(tmp_path):
    """Test saving results to JSON."""
    results = {
        "model_a": {
            "mean_roc_auc": 0.85,
            "std_roc_auc": 0.02,
            "mean_f1": 0.80,
            "std_f1": 0.03
        }
    }
    output_file = tmp_path / "test_metrics.json"
    save_results(results, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == results