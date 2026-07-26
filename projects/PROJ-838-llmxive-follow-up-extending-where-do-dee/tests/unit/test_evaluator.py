import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from evaluator import (
    load_metrics,
    save_metrics,
    load_json_file,
    save_json_file,
    stratified_split,
    calculate_baseline,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_correlation,
    run_sensitivity_analysis_threshold,
    run_sensitivity_analysis_percentile,
    calculate_null_distribution,
    calculate_power_analysis,
    report_comparative_thresholds,
    generate_results_report
)

@pytest.fixture
def sample_train_df():
    """Create a sample training DataFrame."""
    data = {
        'connectivity': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'branching': [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
        'collapse': [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]  # 3 collapse, 7 success
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_test_df():
    """Create a sample test DataFrame."""
    data = {
        'connectivity': [0.15, 0.25, 0.35, 0.45, 0.55],
        'branching': [1.15, 1.25, 1.35, 1.45, 1.55],
        'collapse': [1, 1, 0, 0, 0]
    }
    return pd.DataFrame(data)

def test_20th_percentile_threshold(sample_train_df):
    """Test the calculation of the 20th percentile threshold for the success class."""
    # Success class connectivity: [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # Sorted: [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    # 20th percentile of 7 items: index = 0.2 * (7-1) = 1.2 -> interpolate between 0.5 and 0.6
    # Expected: 0.5 + 0.2 * (0.6 - 0.5) = 0.52
    
    threshold = calculate_20th_percentile_threshold(sample_train_df)
    
    # Using numpy quantile for verification
    success_values = sample_train_df[sample_train_df['collapse'] == 0]['connectivity']
    expected = float(success_values.quantile(0.20))
    
    assert abs(threshold - expected) < 1e-6, f"Expected {expected}, got {threshold}"
    assert threshold > 0.4 and threshold < 0.6, "Threshold should be in the expected range"

def test_20th_percentile_threshold_empty_success(sample_train_df):
    """Test that empty success class raises an error."""
    df = sample_train_df.copy()
    df['collapse'] = 1  # All collapse
    
    with pytest.raises(ValueError, match="No success class samples found"):
        calculate_20th_percentile_threshold(df)

def test_f1_max_threshold(sample_train_df):
    """Test the calculation of the F1-max threshold."""
    threshold = calculate_f1_max_threshold(sample_train_df)
    
    # The threshold should be one of the connectivity values
    assert threshold in sample_train_df['connectivity'].values
    assert threshold >= 0.0
    assert threshold <= 1.0

def test_predict_collapse(sample_test_df):
    """Test the prediction of collapse based on a threshold."""
    threshold = 0.4
    predicted_df = predict_collapse(sample_test_df, threshold)
    
    assert 'predicted_collapse' in predicted_df.columns
    assert len(predicted_df) == len(sample_test_df)
    
    # Check predictions
    # connectivity < 0.4 -> 1 (collapse), else 0
    expected_preds = [1, 1, 0, 0, 0] # 0.15, 0.25 < 0.4; 0.35, 0.45, 0.55 >= 0.4? 
    # Wait: 0.35 < 0.4 is True. So 0.35 -> 1.
    # 0.15 < 0.4 -> 1
    # 0.25 < 0.4 -> 1
    # 0.35 < 0.4 -> 1
    # 0.45 < 0.4 -> 0
    # 0.55 < 0.4 -> 0
    expected_preds = [1, 1, 1, 0, 0]
    
    assert list(predicted_df['predicted_collapse']) == expected_preds

def test_evaluate_performance_metrics(sample_test_df):
    """Test the calculation of performance metrics."""
    threshold = 0.4
    predicted_df = predict_collapse(sample_test_df, threshold)
    metrics = evaluate_performance(predicted_df)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1_score' in metrics
    assert 'accuracy' in metrics
    assert 'confusion_matrix' in metrics
    
    # Verify confusion matrix keys
    cm = metrics['confusion_matrix']
    assert 'tp' in cm
    assert 'tn' in cm
    assert 'fp' in cm
    assert 'fn' in cm

def test_correlation_coefficient_calculation(sample_test_df):
    """Test the calculation of correlation coefficients."""
    # Predict first to ensure columns exist
    threshold = 0.4
    predicted_df = predict_collapse(sample_test_df, threshold)
    
    # Recalculate correlation on original columns
    corr = calculate_correlation(sample_test_df)
    
    assert 'pearson_r' in corr
    assert 'spearman_r' in corr
    assert -1.0 <= corr['pearson_r'] <= 1.0
    assert -1.0 <= corr['spearman_r'] <= 1.0

def test_null_distribution_permutation(sample_test_df):
    """Test the null distribution permutation test."""
    # Predict first
    threshold = 0.4
    predicted_df = predict_collapse(sample_test_df, threshold)
    
    result = calculate_null_distribution(predicted_df, n_permutations=100, seed=42)
    
    assert 'actual_r' in result
    assert 'null_mean' in result
    assert 'null_std' in result
    assert 'p_value' in result
    assert 'sc_002_passed' in result
    assert isinstance(result['sc_002_passed'], bool)

def test_baseline_mean_connectivity(sample_train_df):
    """Test the calculation of baseline mean connectivity."""
    baseline = calculate_baseline(sample_train_df)
    
    success_values = sample_train_df[sample_train_df['collapse'] == 0]['connectivity']
    expected = float(success_values.mean())
    
    assert abs(baseline - expected) < 1e-6

def test_power_analysis_cohen_d(sample_train_df):
    """Test the power analysis calculation."""
    result = calculate_power_analysis(sample_train_df)
    
    assert 'cohens_d' in result
    assert 'power' in result
    assert 'power_sufficient' in result
    assert isinstance(result['power_sufficient'], bool)

def test_stratified_split_preserves_label_ratio_in_metrics_csv(sample_train_df):
    """Test that stratified split preserves label ratio."""
    train_split, test_split = stratified_split(sample_train_df, test_size=0.3, seed=42)
    
    # Check total length
    assert len(train_split) + len(test_split) == len(sample_train_df)
    
    # Check label ratios are roughly preserved
    train_ratio = train_split['collapse'].mean()
    test_ratio = test_split['collapse'].mean()
    original_ratio = sample_train_df['collapse'].mean()
    
    # With small sample, exact preservation is hard, but should be close
    assert abs(train_ratio - original_ratio) < 0.2
    assert abs(test_ratio - original_ratio) < 0.2

def test_save_metrics_writes_csv(tmp_path):
    """Test that save_metrics writes a CSV file."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    filepath = str(tmp_path / "test.csv")
    
    save_metrics(df, filepath)
    
    assert os.path.exists(filepath)
    loaded_df = pd.read_csv(filepath)
    assert loaded_df.equals(df)

def test_load_metrics_reads_csv(tmp_path):
    """Test that load_metrics reads a CSV file."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    filepath = str(tmp_path / "test.csv")
    df.to_csv(filepath, index=False)
    
    loaded_df = load_metrics(filepath)
    assert loaded_df.equals(df)

def test_save_json_file_writes_json(tmp_path):
    """Test that save_json_file writes a JSON file."""
    data = {"key": "value", "num": 42}
    filepath = str(tmp_path / "test.json")
    
    save_json_file(data, filepath)
    
    assert os.path.exists(filepath)
    with open(filepath, 'r') as f:
        loaded_data = json.load(f)
    assert loaded_data == data

def test_load_json_file_reads_json(tmp_path):
    """Test that load_json_file reads a JSON file."""
    data = {"key": "value", "num": 42}
    filepath = str(tmp_path / "test.json")
    with open(filepath, 'w') as f:
        json.dump(data, f)
    
    loaded_data = load_json_file(filepath)
    assert loaded_data == data

def test_run_sensitivity_analysis_threshold(sample_test_df):
    """Test sensitivity analysis over thresholds."""
    thresholds = [0.2, 0.4, 0.6]
    results = run_sensitivity_analysis_threshold(sample_test_df, thresholds)
    
    assert len(results) == len(thresholds)
    for i, res in enumerate(results):
        assert 'threshold' in res
        assert res['threshold'] == thresholds[i]
        assert 'precision' in res
        assert 'recall' in res

def test_run_sensitivity_analysis_percentile(sample_test_df):
    """Test sensitivity analysis over percentiles."""
    percentiles = [0.1, 0.2, 0.3]
    results = run_sensitivity_analysis_percentile(sample_test_df, percentiles)
    
    assert len(results) == len(percentiles)
    for i, res in enumerate(results):
        assert 'percentile' in res
        assert abs(res['percentile'] - percentiles[i]) < 1e-6
        assert 'threshold_value' in res

def test_report_comparative_thresholds():
    """Test the comparative thresholds report generation."""
    threshold_20 = 0.5
    threshold_f1 = 0.6
    sensitivity_thresh = [{"threshold": 0.1}]
    sensitivity_pct = [{"percentile": 0.1}]
    
    report = report_comparative_thresholds(threshold_20, threshold_f1, sensitivity_thresh, sensitivity_pct)
    
    assert report['primary_threshold_20th_percentile'] == threshold_20
    assert report['comparative_threshold_f1_max'] == threshold_f1
    assert report['sensitivity_threshold_matrix'] == sensitivity_thresh
    assert report['sensitivity_percentile_matrix'] == sensitivity_pct
    assert report['difference'] == abs(threshold_20 - threshold_f1)

def test_generate_results_report(sample_test_df):
    """Test the final results report generation."""
    # Prepare inputs
    threshold_20 = 0.5
    threshold_f1 = 0.6
    predicted_df = predict_collapse(sample_test_df, threshold_20)
    baseline = 0.7
    correlation = {'pearson_r': 0.5, 'spearman_r': 0.6}
    null_dist = {'p_value': 0.04, 'sc_002_passed': True}
    linear_reasoning = {'linear_reasoning_confirmed': False}
    power = {'cohens_d': 0.5, 'power': 0.85, 'power_sufficient': True}
    comparative = {'difference': 0.1}
    sensitivity_thresh = []
    sensitivity_pct = []
    
    report = generate_results_report(
        threshold_20, threshold_f1, predicted_df, baseline,
        correlation, null_dist, linear_reasoning, power,
        comparative, sensitivity_thresh, sensitivity_pct
    )
    
    assert 'thresholds' in report
    assert 'baseline' in report
    assert 'performance' in report
    assert 'correlation' in report
    assert 'null_distribution' in report
    assert 'linear_reasoning' in report
    assert 'power_analysis' in report
    assert 'comparative_report' in report
    assert 'sensitivity_analysis' in report
