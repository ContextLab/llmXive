import pytest
import pandas as pd
import json
import os
from pathlib import Path
import tempfile
import numpy as np
from scipy import stats

# Import the functions to test
from code.evaluator import (
    calculate_baseline,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_correlation,
    run_sensitivity_analysis_threshold,
    run_sensitivity_analysis_percentile,
    calculate_null_distribution,
    calculate_linear_reasoning_index,
    calculate_power_analysis,
    report_comparative_thresholds,
    generate_results_report,
    stratified_split,
    load_metrics,
    save_metrics
)

@pytest.fixture
def sample_train_metrics():
    """Create a sample train_metrics.csv for testing."""
    data = {
        'trajectory_id': [1, 2, 3, 4, 5, 6],
        'connectivity': [0.1, 0.2, 0.3, 0.8, 0.9, 1.0],
        'label': ['success', 'success', 'success', 'failure', 'failure', 'failure'],
        'collapse': [0, 0, 0, 1, 1, 1]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def sample_test_metrics():
    """Create a sample test_metrics.csv for testing."""
    data = {
        'trajectory_id': [7, 8, 9, 10],
        'connectivity': [0.15, 0.25, 0.85, 0.95],
        'label': ['success', 'success', 'failure', 'failure'],
        'collapse': [0, 0, 1, 1]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_baseline_mean_connectivity(sample_train_metrics, temp_dir):
    """Test T034: Calculate baseline mean connectivity for success class."""
    # Save sample data
    csv_path = os.path.join(temp_dir, "train_metrics.csv")
    sample_train_metrics.to_csv(csv_path, index=False)
    
    # Run baseline calculation
    result = calculate_baseline(csv_path, success_label="success")
    
    # Verify result
    assert 'baseline_mean_connectivity' in result
    expected_mean = sample_train_metrics[sample_train_metrics['label'] == 'success']['connectivity'].mean()
    assert abs(result['baseline_mean_connectivity'] - expected_mean) < 1e-6

def test_20th_percentile_threshold(sample_train_metrics, temp_dir):
    """Test T030: Calculate 20th percentile threshold."""
    csv_path = os.path.join(temp_dir, "train_metrics.csv")
    sample_train_metrics.to_csv(csv_path, index=False)
    
    result = calculate_20th_percentile_threshold(csv_path, success_label="success")
    
    assert 'threshold_20th_percentile' in result
    expected_threshold = sample_train_metrics[sample_train_metrics['label'] == 'success']['connectivity'].quantile(0.20)
    assert abs(result['threshold_20th_percentile'] - expected_threshold) < 1e-6

def test_f1_max_threshold_calculation(sample_train_metrics, temp_dir):
    """Test T031: Calculate F1-max threshold."""
    csv_path = os.path.join(temp_dir, "train_metrics.csv")
    sample_train_metrics.to_csv(csv_path, index=False)
    
    result = calculate_f1_max_threshold(csv_path, success_label="success")
    
    assert 'f1_max_threshold' in result
    assert 'max_f1_score' in result
    assert 0.0 <= result['f1_max_threshold'] <= 1.0
    assert 0.0 <= result['max_f1_score'] <= 1.0

def test_predict_collapse_threshold_application(sample_test_metrics, temp_dir):
    """Test T032: Apply threshold to predict collapse."""
    csv_path = os.path.join(temp_dir, "test_metrics.csv")
    sample_test_metrics.to_csv(csv_path, index=False)
    
    threshold = 0.5
    result_df = predict_collapse(csv_path, threshold)
    
    assert 'predicted_collapse' in result_df.columns
    # Check predictions: connectivity > 0.5 -> 1 (collapse)
    expected_preds = (sample_test_metrics['connectivity'] > threshold).astype(int)
    assert all(result_df['predicted_collapse'] == expected_preds)

def test_confusion_matrix_metrics(sample_test_metrics, temp_dir):
    """Test T033: Evaluate performance metrics."""
    csv_path = os.path.join(temp_dir, "test_metrics.csv")
    sample_test_metrics.to_csv(csv_path, index=False)
    
    # First predict
    threshold = 0.5
    test_df = predict_collapse(csv_path, threshold)
    
    result = evaluate_performance(test_df)
    
    assert 'precision' in result
    assert 'recall' in result
    assert 'f1_score' in result
    assert 'accuracy' in result
    assert 'confusion_matrix' in result
    
    # Verify confusion matrix values
    cm = result['confusion_matrix']
    assert cm['true_positive'] >= 0
    assert cm['true_negative'] >= 0
    assert cm['false_positive'] >= 0
    assert cm['false_negative'] >= 0

def test_correlation_coefficient_calculation(sample_test_metrics, temp_dir):
    """Test T035: Calculate correlation coefficient."""
    csv_path = os.path.join(temp_dir, "test_metrics.csv")
    sample_test_metrics.to_csv(csv_path, index=False)
    
    result = calculate_correlation(csv_path)
    
    assert 'pearson_r' in result
    assert 'pearson_p' in result
    assert 'spearman_r' in result
    assert 'spearman_p' in result
    
    # Verify ranges
    assert -1.0 <= result['pearson_r'] <= 1.0
    assert -1.0 <= result['spearman_r'] <= 1.0

def test_sensitivity_analysis_threshold(sample_test_metrics, temp_dir):
    """Test T036a: Run sensitivity analysis on thresholds."""
    csv_path = os.path.join(temp_dir, "test_metrics.csv")
    sample_test_metrics.to_csv(csv_path, index=False)
    
    thresholds = [0.1, 0.5, 0.9]
    results = run_sensitivity_analysis_threshold(csv_path, thresholds)
    
    assert len(results) == len(thresholds)
    for res in results:
        assert 'threshold' in res
        assert 'precision' in res
        assert 'recall' in res
        assert 'f1_score' in res

def test_sensitivity_analysis_percentile(sample_test_metrics, temp_dir):
    """Test T036b: Run sensitivity analysis on percentiles."""
    csv_path = os.path.join(temp_dir, "test_metrics.csv")
    sample_test_metrics.to_csv(csv_path, index=False)
    
    percentiles = [10, 20, 30]
    results = run_sensitivity_analysis_percentile(csv_path, percentiles)
    
    assert len(results) == len(percentiles)
    for res in results:
        assert 'percentile' in res
        assert 'threshold' in res
        assert 'precision' in res
        assert 'recall' in res
        assert 'f1_score' in res

def test_linear_reasoning_data_driven(temp_dir):
    """Test T037b: Calculate linear reasoning index."""
    # Create dummy graph files
    graphs_dir = os.path.join(temp_dir, "graphs")
    os.makedirs(graphs_dir)
    
    # Create a chain-like graph
    chain_graph = {
        "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        "edges": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    }
    with open(os.path.join(graphs_dir, "chain.json"), 'w') as f:
        json.dump(chain_graph, f)
        
    # Create a non-chain graph
    non_chain_graph = {
        "nodes": [{"id": "x"}, {"id": "y"}, {"id": "z"}],
        "edges": [{"source": "x", "target": "y"}, {"source": "x", "target": "z"}]
    }
    with open(os.path.join(graphs_dir, "non_chain.json"), 'w') as f:
        json.dump(non_chain_graph, f)
        
    # Create dummy train metrics
    train_df = pd.DataFrame({
        'trajectory_id': [1, 2],
        'connectivity': [0.1, 0.2],
        'label': ['success', 'success']
    })
    train_path = os.path.join(temp_dir, "train_metrics.csv")
    train_df.to_csv(train_path, index=False)
    
    result = calculate_linear_reasoning_index(graphs_dir, train_path)
    
    assert 'linear_reasoning_confirmed' in result
    assert 'threshold_definition' in result
    assert 'chain_ratio' in result
    assert result['chain_ratio'] == 0.5 # 1 chain out of 2

def test_baseline_mean_connectivity_empty_success_class(temp_dir):
    """Test baseline with no success class."""
    data = {
        'trajectory_id': [1, 2],
        'connectivity': [0.8, 0.9],
        'label': ['failure', 'failure']
    }
    df = pd.DataFrame(data)
    csv_path = os.path.join(temp_dir, "train_metrics.csv")
    df.to_csv(csv_path, index=False)
    
    result = calculate_baseline(csv_path, success_label="success")
    assert result['baseline_mean_connectivity'] == 0.0

def test_power_analysis_cohen_d(sample_train_metrics, temp_dir):
    """Test T044: Power analysis with Cohen's d."""
    csv_path = os.path.join(temp_dir, "train_metrics.csv")
    sample_train_metrics.to_csv(csv_path, index=False)
    
    result = calculate_power_analysis(csv_path)
    
    assert 'effect_size' in result
    assert 'power' in result
    assert 'limitation_flag' in result
    assert isinstance(result['limitation_flag'], bool)

def test_stratified_split_preserves_label_ratio_in_metrics_csv(sample_train_metrics, temp_dir):
    """Test T029: Stratified split preserves label distribution."""
    csv_path = os.path.join(temp_dir, "input.csv")
    train_path = os.path.join(temp_dir, "train.csv")
    test_path = os.path.join(temp_dir, "test.csv")
    
    sample_train_metrics.to_csv(csv_path, index=False)
    
    train_df, test_df = stratified_split(csv_path, train_path, test_path, test_size=0.33, random_state=42)
    
    # Check files exist
    assert os.path.exists(train_path)
    assert os.path.exists(test_path)
    
    # Check distributions
    total_ratio = sample_train_metrics['label'].value_counts(normalize=True)
    train_ratio = train_df['label'].value_counts(normalize=True)
    test_ratio = test_df['label'].value_counts(normalize=True)
    
    for label in total_ratio.index:
        assert abs(train_ratio.get(label, 0) - total_ratio[label]) < 0.1
        assert abs(test_ratio.get(label, 0) - total_ratio[label]) < 0.1

def test_comparative_thresholds_report(temp_dir):
    """Test T046: Comparative thresholds report."""
    threshold_config = {"threshold_20th_percentile": 0.2}
    f1_max = {"f1_max_threshold": 0.5}
    sens_thresh = [{"threshold": 0.1, "f1_score": 0.8}]
    sens_perc = [{"percentile": 10, "f1_score": 0.7}]
    
    result = report_comparative_thresholds(threshold_config, f1_max, sens_thresh, sens_perc)
    
    assert 'primary_threshold' in result
    assert 'f1_max_threshold' in result
    assert 'sensitivity_threshold_results' in result
    assert 'comparison_note' in result
    assert result['primary_threshold'] == 0.2