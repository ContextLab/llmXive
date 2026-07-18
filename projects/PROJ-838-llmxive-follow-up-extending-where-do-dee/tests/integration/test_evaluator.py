import pytest
import csv
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluator import (
    load_metrics,
    stratified_split,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_baseline,
    calculate_correlation,
    run_sensitivity_analysis,
    calculate_null_distribution,
    generate_results_report,
    main
)


@pytest.fixture
def setup_metrics_files(tmp_path):
    """Create train and test metrics files for integration testing."""
    # Create data/processed directory structure
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True)
    
    # Create train_metrics.csv
    train_file = data_processed / "train_metrics.csv"
    train_data = [
        {'global_connectivity': 0.1, 'collapse': 1},
        {'global_connectivity': 0.12, 'collapse': 1},
        {'global_connectivity': 0.15, 'collapse': 1},
        {'global_connectivity': 0.18, 'collapse': 1},
        {'global_connectivity': 0.2, 'collapse': 1},
        {'global_connectivity': 0.3, 'collapse': 0},
        {'global_connectivity': 0.4, 'collapse': 0},
        {'global_connectivity': 0.5, 'collapse': 0},
    ]
    
    with open(train_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['global_connectivity', 'collapse'])
        writer.writeheader()
        writer.writerows(train_data)
    
    # Create test_metrics.csv
    test_file = data_processed / "test_metrics.csv"
    test_data = [
        {'global_connectivity': 0.1, 'collapse': 1},
        {'global_connectivity': 0.2, 'collapse': 1},
        {'global_connectivity': 0.3, 'collapse': 0},
        {'global_connectivity': 0.4, 'collapse': 0},
        {'global_connectivity': 0.5, 'collapse': 0},
        {'global_connectivity': 0.15, 'collapse': 1},
        {'global_connectivity': 0.25, 'collapse': 0},
        {'global_connectivity': 0.35, 'collapse': 0},
    ]
    
    with open(test_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['global_connectivity', 'collapse'])
        writer.writeheader()
        writer.writerows(test_data)
    
    return train_file, test_file


def test_full_evaluation_pipeline(setup_metrics_files, tmp_path, monkeypatch):
    """Integration test for the full evaluation pipeline (T030-T037b)."""
    train_file, test_file = setup_metrics_files
    data_processed = train_file.parent
    
    # Change to tmp_path to simulate project root
    monkeypatch.chdir(tmp_path)
    
    # Mock the DATA_PROCESSED path in evaluator module
    import evaluator
    original_data_path = evaluator.DATA_PROCESSED
    evaluator.DATA_PROCESSED = data_processed
    
    try:
        # Re-load metrics to use the new path
        test_metrics = load_metrics(data_processed / "test_metrics.csv")
        train_metrics = load_metrics(data_processed / "train_metrics.csv")
        
        # T030: Calculate thresholds
        threshold_20th = calculate_20th_percentile_threshold(train_metrics)
        threshold_f1_max = calculate_f1_max_threshold(train_metrics)
        
        assert 0.0 < threshold_20th < 1.0
        assert 0.0 < threshold_f1_max < 1.0
        
        # T032: Predict collapse
        predictions = predict_collapse(test_metrics, threshold_20th)
        assert len(predictions) == len(test_metrics)
        assert all('predicted_collapse' in p for p in predictions)
        
        # T033: Evaluate performance
        performance = evaluate_performance(predictions)
        assert 'precision' in performance
        assert 'recall' in performance
        assert 'f1' in performance
        assert 0.0 <= performance['f1'] <= 1.0
        
        # T034: Calculate baseline
        baseline = calculate_baseline(train_metrics)
        assert 0.0 <= baseline <= 1.0
        
        # T035: Calculate correlation
        correlation = calculate_correlation(test_metrics)
        assert -1.0 <= correlation['pearson_r'] <= 1.0
        assert -1.0 <= correlation['spearman_r'] <= 1.0
        
        # T036: Sensitivity analysis
        sensitivity = run_sensitivity_analysis(test_metrics)
        assert 'fixed_thresholds' in sensitivity
        assert 'percentile_thresholds' in sensitivity
        
        # T037a: Null distribution
        null_dist = calculate_null_distribution(test_metrics, n_permutations=50)
        assert 'null_distribution' in null_dist
        assert len(null_dist['null_distribution']) == 50
        assert 0.0 <= null_dist['p_value'] <= 1.0
        
        # T037b: Generate report
        report = generate_results_report(
            threshold_20th, threshold_f1_max, predictions, performance,
            baseline, correlation, sensitivity, null_dist
        )
        
        assert 'thresholds' in report
        assert 'performance' in report
        assert 'correlation' in report
        assert 'sensitivity_analysis' in report
        assert 'null_distribution_test' in report
        
        # Verify report can be serialized
        report_json = json.dumps(report)
        assert len(report_json) > 0
        
    finally:
        # Restore original path
        evaluator.DATA_PROCESSED = original_data_path