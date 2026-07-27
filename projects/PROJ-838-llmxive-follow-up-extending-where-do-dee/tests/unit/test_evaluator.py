import pytest
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from evaluator import (
    load_metrics,
    save_metrics,
    stratified_split,
    verify_split_distribution,
    calculate_baseline,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_correlation,
    calculate_null_distribution,
    calculate_linear_reasoning_index,
    calculate_power_analysis,
    report_comparative_thresholds,
    generate_results_report
)

@pytest.fixture
def sample_metrics_csv(tmp_path):
    """Create a sample metrics CSV file."""
    data = {
        'trajectory_id': ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8'],
        'global_connectivity': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'avg_branching_factor': [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4],
        'label': ['success', 'success', 'failure', 'failure', 'success', 'failure', 'success', 'failure']
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "metrics.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path), df

def test_stratified_split_preserves_label_ratio_in_metrics_csv(sample_metrics_csv, tmp_path):
    """
    Test that stratified_split creates train/test sets with correct label distribution.
    """
    csv_path, original_df = sample_metrics_csv
    train_path = str(tmp_path / "train_metrics.csv")
    test_path = str(tmp_path / "test_metrics.csv")
    
    # Perform split
    train_df, test_df = stratified_split(csv_path, train_path, test_path, test_size=0.25, random_state=42)
    
    # Verify files exist
    assert os.path.exists(train_path), "Train CSV not created"
    assert os.path.exists(test_path), "Test CSV not created"
    
    # Verify label distribution within 5% tolerance
    is_valid = verify_split_distribution(original_df, train_df, test_df, tolerance=0.05)
    assert is_valid, "Label distribution mismatch between original and splits"
    
    # Verify sizes (approximate due to small sample size)
    assert len(train_df) + len(test_df) == len(original_df)

def test_stratified_split_fails_on_missing_file(tmp_path):
    """Test that stratified_split raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        stratified_split("nonexistent.csv", str(tmp_path / "train.csv"), str(tmp_path / "test.csv"))

def test_stratified_split_fails_on_missing_label_column(tmp_path):
    """Test that stratified_split raises ValueError if 'label' column is missing."""
    data = {'id': [1, 2, 3], 'value': [0.1, 0.2, 0.3]}
    df = pd.DataFrame(data)
    csv_path = tmp_path / "no_label.csv"
    df.to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError):
        stratified_split(str(csv_path), str(tmp_path / "train.csv"), str(tmp_path / "test.csv"))

def test_verify_split_distribution():
    """Test verify_split_distribution with perfect and imperfect splits."""
    orig = pd.DataFrame({'label': ['A', 'A', 'B', 'B']})
    train = pd.DataFrame({'label': ['A', 'B']})
    test = pd.DataFrame({'label': ['A', 'B']})
    
    assert verify_split_distribution(orig, train, test, tolerance=0.05) is True
    
    # Imperfect split
    train_bad = pd.DataFrame({'label': ['A', 'A']})
    test_bad = pd.DataFrame({'label': ['B', 'B']})
    assert verify_split_distribution(orig, train_bad, test_bad, tolerance=0.05) is False

def test_calculate_baseline(sample_metrics_csv):
    """Test calculation of baseline mean connectivity for success class."""
    _, df = sample_metrics_csv
    baseline = calculate_baseline(df)
    
    success_df = df[df['label'] == 'success']
    expected = success_df['global_connectivity'].mean()
    
    assert baseline == expected

def test_calculate_20th_percentile_threshold(sample_metrics_csv):
    """Test calculation of 20th percentile threshold."""
    _, df = sample_metrics_csv
    threshold = calculate_20th_percentile_threshold(df)
    
    success_df = df[df['label'] == 'success']
    combined = pd.concat([success_df['global_connectivity'], success_df['avg_branching_factor']])
    expected = combined.quantile(0.20)
    
    assert abs(threshold - expected) < 1e-6

def test_calculate_20th_percentile_threshold_few_samples(sample_metrics_csv, tmp_path):
    """Test that 20th percentile calculation fails with fewer than 5 samples."""
    data = {
        'trajectory_id': ['t1', 't2', 't3'],
        'global_connectivity': [0.1, 0.2, 0.3],
        'avg_branching_factor': [1.0, 1.2, 1.4],
        'label': ['success', 'success', 'success']
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "few_samples.csv"
    df.to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError, match="fewer than 5 samples"):
        calculate_20th_percentile_threshold(df)

def test_calculate_f1_max_threshold(sample_metrics_csv):
    """Test calculation of F1-max threshold."""
    _, df = sample_metrics_csv
    threshold = calculate_f1_max_threshold(df)
    
    # Basic sanity check: threshold should be within the range of connectivity values
    assert df['global_connectivity'].min() <= threshold <= df['global_connectivity'].max()

def test_predict_collapse(sample_metrics_csv):
    """Test prediction of collapse based on threshold."""
    _, df = sample_metrics_csv
    threshold = 0.45
    predictions = predict_collapse(df, threshold)
    
    # Values < 0.45 should be 1 (collapse), others 0
    expected = (df['global_connectivity'] < threshold).astype(int)
    assert list(predictions) == list(expected)

def test_evaluate_performance(sample_metrics_csv):
    """Test evaluation of performance metrics."""
    _, df = sample_metrics_csv
    threshold = 0.45
    predictions = predict_collapse(df, threshold)
    metrics = evaluate_performance(df, predictions)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert 'accuracy' in metrics
    assert 'confusion_matrix' in metrics

def test_calculate_correlation(sample_metrics_csv):
    """Test calculation of correlation coefficient."""
    _, df = sample_metrics_csv
    corr = calculate_correlation(df)
    
    assert isinstance(corr, float)
    assert -1.0 <= corr <= 1.0

def test_calculate_null_distribution(sample_metrics_csv):
    """Test null distribution calculation."""
    _, df = sample_metrics_csv
    result = calculate_null_distribution(df, n_permutations=100, random_state=42)
    
    assert 'observed_correlation' in result
    assert 'p_value' in result
    assert 'significant' in result
    assert 'null_distribution_mean' in result
    assert 'null_distribution_std' in result

def test_calculate_linear_reasoning_index(tmp_path):
    """Test linear reasoning index calculation."""
    # Create a simple linear graph: A -> B -> C
    graph_data = {
        'nodes': ['A', 'B', 'C'],
        'edges': [['A', 'B'], ['B', 'C']]
    }
    graph_path = tmp_path / "linear_graph.json"
    with open(graph_path, 'w') as f:
        json.dump(graph_data, f)
    
    index = calculate_linear_reasoning_index(str(graph_path))
    
    # 3 nodes, 2 edges. B has in=1, out=1. A has out=1, in=0. C has in=1, out=0.
    # Only B satisfies in=1 and out=1. So 1/3.
    assert abs(index - 1/3) < 1e-6

def test_calculate_linear_reasoning_index_non_linear(tmp_path):
    """Test linear reasoning index for a non-linear graph."""
    # Create a star graph: A -> B, A -> C
    graph_data = {
        'nodes': ['A', 'B', 'C'],
        'edges': [['A', 'B'], ['A', 'C']]
    }
    graph_path = tmp_path / "star_graph.json"
    with open(graph_path, 'w') as f:
        json.dump(graph_data, f)
    
    index = calculate_linear_reasoning_index(str(graph_path))
    
    # Edges (2) != Nodes - 1 (2) -> Wait, 3-1=2. Condition met.
    # But no node has in=1 AND out=1.
    # A: out=2, B: in=1, C: in=1.
    # So index = 0.
    assert index == 0.0

def test_calculate_power_analysis(sample_metrics_csv):
    """Test power analysis calculation."""
    _, df = sample_metrics_csv
    result = calculate_power_analysis(df)
    
    assert 'effect_size' in result
    assert 'power' in result
    assert 'limitation_flag' in result

def test_report_comparative_thresholds():
    """Test comparative thresholds report generation."""
    threshold_config = {'threshold': 0.25}
    f1_max = {'threshold': 0.30}
    sens_thresh = {'0.1': {'f1': 0.5}}
    sens_perc = {'20': {'f1': 0.6}}
    
    report = report_comparative_thresholds(threshold_config, f1_max, sens_thresh, sens_perc)
    
    assert report['primary_threshold'] == 0.25
    assert report['f1_max_threshold'] == 0.30
    assert 'sensitivity_threshold_matrix' in report

def test_generate_results_report():
    """Test final results report generation."""
    baseline = {'mean': 0.5}
    threshold_config = {'threshold': 0.25}
    f1_max = {'threshold': 0.30}
    sens_thresh = {}
    sens_perc = {}
    test_df = pd.DataFrame({'label': ['success', 'failure'], 'global_connectivity': [0.1, 0.9]})
    predictions = pd.Series([1, 0])
    perf = {'f1': 0.8}
    corr = 0.9
    null_dist = {'significant': True}
    linear_report = {'confirmed': True}
    power = {'limitation_flag': False}
    
    report = generate_results_report(
        baseline, threshold_config, f1_max, sens_thresh, sens_perc,
        test_df, predictions, perf, corr, null_dist, linear_report, power
    )
    
    assert 'baseline' in report
    assert 'test_performance' in report
    assert 'summary' in report
