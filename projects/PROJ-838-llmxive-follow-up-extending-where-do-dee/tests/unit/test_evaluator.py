import pytest
import os
import json
import csv
from pathlib import Path
from evaluator import (
    load_metrics, save_metrics, load_json_file, save_json_file,
    stratified_split, calculate_baseline, calculate_20th_percentile_threshold,
    calculate_f1_max_threshold, predict_collapse, evaluate_performance,
    calculate_correlation, run_sensitivity_analysis, calculate_null_distribution,
    calculate_linear_reasoning_index, calculate_power_analysis, report_comparative_thresholds,
    generate_results_report
)

@pytest.fixture
def sample_test_metrics():
    """Fixture providing sample test metrics data."""
    return [
        {'trajectory_id': 't1', 'connectivity': 0.05, 'branching_factor': 1.2, 'collapse': True, 'predicted_collapse': False},
        {'trajectory_id': 't2', 'connectivity': 0.02, 'branching_factor': 1.1, 'collapse': True, 'predicted_collapse': True},
        {'trajectory_id': 't3', 'connectivity': 0.08, 'branching_factor': 1.5, 'collapse': False, 'predicted_collapse': False},
        {'trajectory_id': 't4', 'connectivity': 0.01, 'branching_factor': 1.0, 'collapse': False, 'predicted_collapse': True},
        {'trajectory_id': 't5', 'connectivity': 0.06, 'branching_factor': 1.3, 'collapse': True, 'predicted_collapse': True},
    ]

@pytest.fixture
def sample_train_metrics():
    """Fixture providing sample train metrics data."""
    return [
        {'trajectory_id': 'tr1', 'connectivity': 0.04, 'branching_factor': 1.2, 'collapse': False},
        {'trajectory_id': 'tr2', 'connectivity': 0.03, 'branching_factor': 1.1, 'collapse': False},
        {'trajectory_id': 'tr3', 'connectivity': 0.09, 'branching_factor': 1.5, 'collapse': False},
        {'trajectory_id': 'tr4', 'connectivity': 0.01, 'branching_factor': 1.0, 'collapse': False},
        {'trajectory_id': 'tr5', 'connectivity': 0.07, 'branching_factor': 1.3, 'collapse': True},
        {'trajectory_id': 'tr6', 'connectivity': 0.02, 'branching_factor': 1.1, 'collapse': True},
    ]

def test_evaluate_performance_metrics(sample_test_metrics):
    """Test that evaluate_performance returns correct Precision, Recall, F1, and Confusion Matrix."""
    # Correct predictions manually:
    # t1: True collapse, False pred -> FN
    # t2: True collapse, True pred -> TP
    # t3: False collapse, False pred -> TN
    # t4: False collapse, True pred -> FP
    # t5: True collapse, True pred -> TP
    # TP=2, TN=1, FP=1, FN=1
    # Precision = TP / (TP+FP) = 2/3
    # Recall = TP / (TP+FN) = 2/3
    # F1 = 2 * (P*R)/(P+R) = 2/3
    
    result = evaluate_performance(sample_test_metrics)
    
    assert 'precision' in result
    assert 'recall' in result
    assert 'f1' in result
    assert 'confusion_matrix' in result
    assert 'support' in result
    
    assert result['support'] == 5
    assert abs(result['precision'] - (2/3)) < 0.01
    assert abs(result['recall'] - (2/3)) < 0.01
    assert abs(result['f1'] - (2/3)) < 0.01
    
    cm = result['confusion_matrix']
    # Confusion matrix format: [[TN, FP], [FN, TP]]
    # Expected: [[1, 1], [1, 2]]
    assert cm[0][0] == 1 # TN
    assert cm[0][1] == 1 # FP
    assert cm[1][0] == 1 # FN
    assert cm[1][1] == 2 # TP

def test_evaluate_performance_empty_data():
    """Test evaluate_performance with empty input."""
    result = evaluate_performance([])
    assert result['precision'] == 0.0
    assert result['recall'] == 0.0
    assert result['f1'] == 0.0
    assert result['confusion_matrix'] == [[0, 0], [0, 0]]
    assert result['support'] == 0

def test_predict_collapse_threshold_application(sample_test_metrics):
    """Test that predict_collapse correctly applies the threshold."""
    threshold = 0.04
    result = predict_collapse(sample_test_metrics, threshold)
    
    # t1: 0.05 < 0.04? False
    # t2: 0.02 < 0.04? True
    # t3: 0.08 < 0.04? False
    # t4: 0.01 < 0.04? True
    # t5: 0.06 < 0.04? False
    
    assert result[0]['predicted_collapse'] == False
    assert result[1]['predicted_collapse'] == True
    assert result[2]['predicted_collapse'] == False
    assert result[3]['predicted_collapse'] == True
    assert result[4]['predicted_collapse'] == False