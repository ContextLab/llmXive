import pytest
import csv
import os
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr, spearmanr

# Import functions from the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluator import (
    load_metrics,
    save_metrics,
    stratified_split,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_baseline,
    calculate_correlation,
    run_sensitivity_analysis,
    calculate_null_distribution
)


@pytest.fixture
def sample_test_metrics(tmp_path):
    """Create a sample test_metrics.csv file."""
    filepath = tmp_path / "test_metrics.csv"
    data = [
        {'global_connectivity': 0.1, 'collapse': 1},
        {'global_connectivity': 0.2, 'collapse': 1},
        {'global_connectivity': 0.3, 'collapse': 0},
        {'global_connectivity': 0.4, 'collapse': 0},
        {'global_connectivity': 0.5, 'collapse': 0},
        {'global_connectivity': 0.15, 'collapse': 1},
        {'global_connectivity': 0.25, 'collapse': 0},
        {'global_connectivity': 0.35, 'collapse': 0},
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['global_connectivity', 'collapse'])
        writer.writeheader()
        writer.writerows(data)
    
    return filepath


@pytest.fixture
def sample_train_metrics(tmp_path):
    """Create a sample train_metrics.csv file."""
    filepath = tmp_path / "train_metrics.csv"
    data = [
        {'global_connectivity': 0.1, 'collapse': 1},
        {'global_connectivity': 0.12, 'collapse': 1},
        {'global_connectivity': 0.15, 'collapse': 1},
        {'global_connectivity': 0.18, 'collapse': 1},
        {'global_connectivity': 0.2, 'collapse': 1},
        {'global_connectivity': 0.3, 'collapse': 0},
        {'global_connectivity': 0.4, 'collapse': 0},
        {'global_connectivity': 0.5, 'collapse': 0},
    ]
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['global_connectivity', 'collapse'])
        writer.writeheader()
        writer.writerows(data)
    
    return filepath


def test_load_metrics(sample_test_metrics):
    """Test loading metrics from CSV."""
    metrics = load_metrics(sample_test_metrics)
    assert len(metrics) == 8
    assert metrics[0]['global_connectivity'] == 0.1
    assert metrics[0]['collapse'] == 1


def test_stratified_split(sample_train_metrics):
    """Test stratified split preserves label balance."""
    train_data = load_metrics(sample_train_metrics)
    train_split, test_split = stratified_split(train_data, test_size=0.25)
    
    # Check split sizes (approximate)
    assert len(train_split) + len(test_split) == 8
    
    # Check label balance in both splits
    train_success = sum(1 for m in train_split if m['collapse'] == 1)
    test_success = sum(1 for m in test_split if m['collapse'] == 1)
    
    assert train_success > 0
    assert test_success > 0


def test_calculate_20th_percentile_threshold(sample_train_metrics):
    """Test 20th percentile threshold calculation."""
    train_data = load_metrics(sample_train_metrics)
    threshold = calculate_20th_percentile_threshold(train_data)
    
    # Success values: [0.1, 0.12, 0.15, 0.18, 0.2]
    # Sorted: same
    # 20th percentile index: int(0.2 * 5) = 1 -> value 0.12
    assert abs(threshold - 0.12) < 0.001


def test_calculate_f1_max_threshold(sample_train_metrics):
    """Test F1-max threshold calculation."""
    train_data = load_metrics(sample_train_metrics)
    threshold = calculate_f1_max_threshold(train_data)
    
    # Should return a valid threshold from the data
    assert threshold is not None
    assert 0.0 <= threshold <= 1.0


def test_predict_collapse(sample_test_metrics):
    """Test collapse prediction logic."""
    test_data = load_metrics(sample_test_metrics)
    threshold = 0.25
    
    predictions = predict_collapse(test_data, threshold)
    
    # Check that predicted_collapse is added
    assert 'predicted_collapse' in predictions[0]
    
    # Check logic: val < threshold -> 1 (collapse), else 0
    assert predictions[0]['predicted_collapse'] == 1  # 0.1 < 0.25
    assert predictions[2]['predicted_collapse'] == 0  # 0.3 >= 0.25


def test_evaluate_performance(sample_test_metrics):
    """Test performance evaluation metrics."""
    test_data = load_metrics(sample_test_metrics)
    predictions = predict_collapse(test_data, threshold=0.25)
    metrics = evaluate_performance(predictions)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert 'confusion_matrix' in metrics
    
    # Check confusion matrix keys
    cm = metrics['confusion_matrix']
    assert 'tp' in cm
    assert 'fp' in cm
    assert 'tn' in cm
    assert 'fn' in cm


def test_calculate_baseline(sample_train_metrics):
    """Test baseline calculation (mean success connectivity)."""
    train_data = load_metrics(sample_train_metrics)
    baseline = calculate_baseline(train_data)
    
    # Success values: [0.1, 0.12, 0.15, 0.18, 0.2]
    # Mean: 0.15
    assert abs(baseline - 0.15) < 0.001


def test_calculate_correlation(sample_test_metrics):
    """Test correlation calculation (T035)."""
    test_data = load_metrics(sample_test_metrics)
    result = calculate_correlation(test_data)
    
    assert 'pearson_r' in result
    assert 'pearson_p' in result
    assert 'spearman_r' in result
    assert 'spearman_p' in result
    
    # Check that correlations are within valid range [-1, 1]
    assert -1.0 <= result['pearson_r'] <= 1.0
    assert -1.0 <= result['spearman_r'] <= 1.0
    
    # Check p-values are within [0, 1]
    assert 0.0 <= result['pearson_p'] <= 1.0
    assert 0.0 <= result['spearman_p'] <= 1.0


def test_run_sensitivity_analysis(sample_test_metrics):
    """Test sensitivity analysis."""
    test_data = load_metrics(sample_test_metrics)
    result = run_sensitivity_analysis(test_data)
    
    assert 'fixed_thresholds' in result
    assert 'percentile_thresholds' in result
    
    # Check fixed thresholds
    assert 0.01 in result['fixed_thresholds']
    assert 0.05 in result['fixed_thresholds']
    assert 0.1 in result['fixed_thresholds']
    
    # Check percentile thresholds
    assert 10 in result['percentile_thresholds']
    assert 20 in result['percentile_thresholds']


def test_calculate_null_distribution(sample_test_metrics):
    """Test null distribution calculation."""
    test_data = load_metrics(sample_test_metrics)
    result = calculate_null_distribution(test_data, n_permutations=100)
    
    assert 'null_distribution' in result
    assert 'observed_r' in result
    assert 'p_value' in result
    assert 'pass_fail' in result
    
    # Check null distribution length
    assert len(result['null_distribution']) == 100
    
    # Check p-value range
    assert 0.0 <= result['p_value'] <= 1.0
    
    # Check pass_fail is boolean
    assert isinstance(result['pass_fail'], bool)
