import pytest
import os
import json
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from evaluator import (
    load_metrics, save_metrics, stratified_split,
    calculate_baseline, calculate_20th_percentile_threshold,
    calculate_f1_max_threshold, predict_collapse, evaluate_performance
)

@pytest.fixture
def sample_train_data(tmp_path):
    """Create a sample training dataset for testing."""
    data = [
        {'trajectory_id': 't1', 'connectivity': 0.1, 'avg_branching': 1.2, 'label': 1},
        {'trajectory_id': 't2', 'connectivity': 0.2, 'avg_branching': 1.5, 'label': 1},
        {'trajectory_id': 't3', 'connectivity': 0.3, 'avg_branching': 1.8, 'label': 1},
        {'trajectory_id': 't4', 'connectivity': 0.4, 'avg_branching': 2.0, 'label': 1},
        {'trajectory_id': 't5', 'connectivity': 0.5, 'avg_branching': 2.2, 'label': 1},
        {'trajectory_id': 't6', 'connectivity': 0.05, 'avg_branching': 0.8, 'label': 0},
        {'trajectory_id': 't7', 'connectivity': 0.15, 'avg_branching': 0.9, 'label': 0},
        {'trajectory_id': 't8', 'connectivity': 0.25, 'avg_branching': 1.0, 'label': 0},
    ]
    return data

@pytest.fixture
def sample_test_data(tmp_path):
    """Create a sample test dataset for testing."""
    data = [
        {'trajectory_id': 't9', 'connectivity': 0.12, 'avg_branching': 1.3, 'label': 1},
        {'trajectory_id': 't10', 'connectivity': 0.18, 'avg_branching': 1.4, 'label': 1},
        {'trajectory_id': 't11', 'connectivity': 0.08, 'avg_branching': 0.7, 'label': 0},
    ]
    return data

def test_stratified_split(sample_train_data):
    train, test = stratified_split(sample_train_data, test_ratio=0.2, seed=42)
    assert len(train) + len(test) == len(sample_train_data)
    # Check label balance roughly
    train_labels = [d['label'] for d in train]
    test_labels = [d['label'] for d in test]
    assert sum(train_labels) + sum(test_labels) == 5 # Total 5 success in sample
    assert sum([1 for l in train_labels if l == 0]) + sum([1 for l in test_labels if l == 0]) == 3 # Total 3 failure

def test_calculate_20th_percentile_threshold(sample_train_data, tmp_path):
    output_path = str(tmp_path / 'threshold_config.json')
    calculate_20th_percentile_threshold(sample_train_data, output_path)

    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        result = json.load(f)

    assert 'threshold_value' in result
    assert result['threshold_type'] == '20th_percentile_success'
    # Verify calculation manually:
    # Success values: [0.1, 0.2, 0.3, 0.4, 0.5]
    # 20th percentile of these 5 values
    # np.percentile([0.1, 0.2, 0.3, 0.4, 0.5], 20) = 0.14 (linear interpolation)
    expected = float(np.percentile([0.1, 0.2, 0.3, 0.4, 0.5], 20))
    assert abs(result['threshold_value'] - expected) < 1e-6

def test_calculate_f1_max_threshold(sample_train_data, tmp_path):
    output_path = str(tmp_path / 'f1_max_threshold.json')
    calculate_f1_max_threshold(sample_train_data, output_path)

    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        result = json.load(f)

    assert 'threshold_value' in result
    assert 'max_f1_score' in result
    # The threshold should be one of the unique connectivity values
    unique_vals = sorted(list(set([d['connectivity'] for d in sample_train_data])))
    assert result['threshold_value'] in unique_vals

def test_predict_collapse(sample_test_data, tmp_path):
    threshold = 0.15
    output_path = str(tmp_path / 'predictions.csv')
    predict_collapse(sample_test_data, threshold, output_path)

    assert os.path.exists(output_path)
    loaded = load_metrics(output_path)
    assert len(loaded) == len(sample_test_data)
    for row in loaded:
        assert 'prediction' in row
        if row['connectivity'] < threshold:
            assert row['prediction'] == 0
        else:
            assert row['prediction'] == 1

def test_evaluate_performance(sample_test_data, tmp_path):
    # First create predictions
    threshold = 0.15
    preds_path = str(tmp_path / 'predictions.csv')
    predict_collapse(sample_test_data, threshold, preds_path)

    # Then evaluate
    perf_path = str(tmp_path / 'performance.json')
    evaluate_performance(sample_test_data, preds_path, perf_path)

    assert os.path.exists(perf_path)
    with open(perf_path, 'r') as f:
        result = json.load(f)

    assert 'precision' in result
    assert 'recall' in result
    assert 'f1_score' in result
    assert 'confusion_matrix' in result
    assert 'true_positive' in result['confusion_matrix']
    assert 'false_positive' in result['confusion_matrix']
    assert 'true_negative' in result['confusion_matrix']
    assert 'false_negative' in result['confusion_matrix']
