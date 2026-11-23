import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from eval.aggregator import (
    load_experiment_results,
    load_baseline_metrics,
    aggregate_benchmark_report,
    save_report,
    run_aggregation
)

@pytest.fixture
def temp_results_dir(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    # Create mock heuristic results
    mock_data = {
        "f1_score": 0.85,
        "perplexity": 12.5,
        "selected_blocks": [1, 2, 3, 4, 5],
        "per_sample_f1": [0.8, 0.85, 0.9, 0.82, 0.88]
    }
    
    with open(results_dir / "entropy_results.json", 'w') as f:
        json.dump(mock_data, f)
        
    with open(results_dir / "gradient_results.json", 'w') as f:
        mock_data["f1_score"] = 0.82
        mock_data["per_sample_f1"] = [0.78, 0.82, 0.85, 0.80, 0.86]
        json.dump(mock_data, f)
        
    return results_dir

@pytest.fixture
def temp_baseline_file(tmp_path):
    baseline_file = tmp_path / "baseline_metrics.json"
    baseline_data = {
        "f1_score": 0.90,
        "perplexity": 10.2,
        "baseline_selected_blocks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "per_sample_f1": [0.88, 0.90, 0.92, 0.89, 0.91]
    }
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f)
    return baseline_file

def test_load_experiment_results(temp_results_dir):
    results = load_experiment_results(temp_results_dir)
    assert "entropy" in results
    assert "gradient" in results
    assert abs(results["entropy"]["f1_score"] - 0.85) < 1e-5

def test_load_baseline_metrics(temp_baseline_file):
    baseline = load_baseline_metrics(temp_baseline_file)
    assert abs(baseline["f1_score"] - 0.90) < 1e-5
    assert len(baseline["baseline_selected_blocks"]) == 10

def test_aggregate_benchmark_report_schema(temp_results_dir, temp_baseline_file):
    """
    Test that the aggregated report contains all required keys:
    f1_score, p_value, false_positive_rate, sensitivity_table, ttest_stat, wilcoxon_stat, significance_statement
    """
    heuristic_results = load_experiment_results(temp_results_dir)
    baseline_metrics = load_baseline_metrics(temp_baseline_file)
    
    report = aggregate_benchmark_report(heuristic_results, baseline_metrics)
    
    required_keys = [
        "f1_score",
        "p_value",
        "false_positive_rate",
        "sensitivity_table",
        "ttest_stat",
        "wilcoxon_stat",
        "significance_statement"
    ]
    
    for key in required_keys:
        assert key in report, f"Missing required key: {key}"
    
    # Check types
    assert isinstance(report["f1_score"], dict)
    assert isinstance(report["p_value"], dict)
    assert isinstance(report["false_positive_rate"], dict)
    assert isinstance(report["sensitivity_table"], list)
    assert isinstance(report["ttest_stat"], dict)
    assert isinstance(report["wilcoxon_stat"], dict)
    assert isinstance(report["significance_statement"], str)

def test_aggregate_false_positive_rate(temp_results_dir, temp_baseline_file):
    heuristic_results = load_experiment_results(temp_results_dir)
    baseline_metrics = load_baseline_metrics(temp_baseline_file)
    
    report = aggregate_benchmark_report(heuristic_results, baseline_metrics)
    
    # Entropy selected [1,2,3,4,5], Baseline selected [1..10]
    # False positives: Heuristic selected but NOT in Baseline -> None (all 1-5 are in 1-10)
    # So FPR should be 0.0
    assert report["false_positive_rate"]["entropy"] == 0.0

def test_save_report(tmp_path):
    report = {
        "f1_score": {"test": 0.5},
        "p_value": {"test": 0.01},
        "false_positive_rate": {"test": 0.0},
        "sensitivity_table": [],
        "ttest_stat": {"test": 1.0},
        "wilcoxon_stat": {"test": 1.0},
        "significance_statement": "p < 0.05"
    }
    output_file = tmp_path / "test_report.json"
    
    save_report(report, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    assert loaded == report

def test_run_aggregation_integration(temp_results_dir, temp_baseline_file, tmp_path):
    output_file = tmp_path / "final_report.json"
    
    result = run_aggregation(
        temp_results_dir,
        temp_baseline_file,
        output_file,
        thresholds=[0.01, 0.05]
    )
    
    assert result is not None
    assert output_file.exists()
    
    # Verify keys again
    required_keys = [
        "f1_score", "p_value", "false_positive_rate", 
        "sensitivity_table", "ttest_stat", "wilcoxon_stat", 
        "significance_statement"
    ]
    for key in required_keys:
        assert key in result