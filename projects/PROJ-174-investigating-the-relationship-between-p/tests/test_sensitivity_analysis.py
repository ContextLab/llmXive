import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.sensitivity_analysis import (
    load_classification_predictions,
    compute_metrics_at_threshold,
    calculate_stability_metrics,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_predictions(tmp_path):
    """Create a sample predictions file for testing."""
    data = {
        'subject_id': ['S1', 'S1', 'S2', 'S2', 'S2'],
        'trial_id': [1, 2, 1, 2, 3],
        'predicted_prob': [0.1, 0.4, 0.6, 0.8, 0.9],
        'true_label': [0, 0, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "predictions.csv"
    df.to_csv(path, index=False)
    return str(path)

@pytest.fixture
def sample_config(tmp_path):
    """Create a sample config file."""
    data = {
        'seeds': [42],
        'thresholds': [0.3, 0.5, 0.7],
        'paths': {'data': 'data'},
        'aggregation': False
    }
    path = tmp_path / "config.yaml"
    with open(path, 'w') as f:
        import yaml
        yaml.dump(data, f)
    return str(path)

def test_load_classification_predictions(sample_predictions):
    df = load_classification_predictions(sample_predictions)
    assert 'predicted_prob' in df.columns
    assert 'true_label' in df.columns
    assert len(df) == 5

def test_compute_metrics_at_threshold(sample_predictions):
    df = pd.read_csv(sample_predictions)
    
    # Threshold 0.2: All 0.4, 0.6, 0.8, 0.9 are >= 0.2 -> 4 preds = 1
    # True: 0, 0, 1, 1, 1
    # Pred: 1, 1, 1, 1, 1
    # Acc: 3/5 = 0.6
    metrics = compute_metrics_at_threshold(df, 0.2)
    assert 'accuracy' in metrics
    assert 'auc' in metrics
    assert metrics['accuracy'] == 0.6  # 3 correct out of 5

def test_calculate_stability_metrics():
    # Create mock results
    results = [
        {'threshold': 0.4, 'accuracy': 0.8, 'auc': 0.90},
        {'threshold': 0.5, 'accuracy': 0.85, 'auc': 0.90}, # Same AUC
        {'threshold': 0.6, 'accuracy': 0.82, 'auc': 0.90}
    ]
    
    final = calculate_stability_metrics(results)
    assert len(final) == 3
    assert all(r['stability_status'] == 'PASS' for r in final)
    assert all(r['relative_decrease'] == 0.0 for r in final)

def test_calculate_stability_metrics_fail():
    # Create mock results with high variance in AUC
    results = [
        {'threshold': 0.4, 'accuracy': 0.8, 'auc': 1.0},
        {'threshold': 0.5, 'accuracy': 0.85, 'auc': 0.50} # Huge drop
    ]
    
    final = calculate_stability_metrics(results)
    # Drop is 50%, which is > 5%
    assert all(r['stability_status'] == 'FAIL' for r in final)
    assert final[0]['relative_decrease'] == 0.5

def test_run_sensitivity_analysis_integration(tmp_path, sample_predictions):
    output_path = str(tmp_path / "sensitivity_analysis.csv")
    thresholds = [0.3, 0.5, 0.7]
    
    df = run_sensitivity_analysis(sample_predictions, output_path, thresholds)
    
    assert os.path.exists(output_path)
    result_df = pd.read_csv(output_path)
    
    assert 'threshold' in result_df.columns
    assert 'accuracy' in result_df.columns
    assert 'auc' in result_df.columns
    assert 'stability_status' in result_df.columns
    assert len(result_df) == 3