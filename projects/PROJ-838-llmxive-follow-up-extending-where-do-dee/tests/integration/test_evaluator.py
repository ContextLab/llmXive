import pytest
import pandas as pd
import json
from pathlib import Path
import os
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from evaluator import (
    stratified_split,
    calculate_baseline,
    calculate_20th_percentile_threshold,
    calculate_f1_max_threshold,
    predict_collapse,
    evaluate_performance,
    calculate_correlation,
    calculate_null_distribution,
    calculate_power_analysis,
    report_comparative_thresholds,
    generate_results_report
)

@pytest.fixture
def full_metrics_csv(tmp_path):
    """Create a comprehensive metrics CSV for integration testing."""
    # Create a dataset with clear separation between success and failure
    data = {
        'trajectory_id': [f't{i}' for i in range(1, 101)],
        'connectivity': list(range(1, 51)) + list(range(60, 110)),  # Low for success, high for failure
        'branching': [1.0 + i * 0.02 for i in range(50)] + [2.0 + i * 0.02 for i in range(50)],
        'collapse': [0] * 50 + [1] * 50  # First 50 success, next 50 failure
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "metrics.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_full_prediction_pipeline(full_metrics_csv, tmp_path):
    """Integration test for the full prediction pipeline."""
    train_output = tmp_path / "train_metrics.csv"
    test_output = tmp_path / "test_metrics.csv"
    baseline_output = tmp_path / "baseline_report.json"
    threshold_output = tmp_path / "threshold_config.json"
    f1_output = tmp_path / "f1_max_threshold.json"
    results_output = tmp_path / "results_report.json"
    
    # Step 1: Stratified split
    train_df, test_df = stratified_split(
        full_metrics_csv,
        str(train_output),
        str(test_output),
        test_size=0.2,
        random_state=42
    )
    
    # Verify splits
    assert train_output.exists()
    assert test_output.exists()
    assert len(train_df) > len(test_df)
    assert 'collapse' in train_df.columns
    assert 'collapse' in test_df.columns
    
    # Step 2: Calculate baseline
    baseline = calculate_baseline(train_df)
    with open(baseline_output, 'w') as f:
        json.dump({'baseline_mean_connectivity': baseline}, f)
    
    # Step 3: Calculate 20th percentile threshold
    threshold_20th = calculate_20th_percentile_threshold(train_df)
    with open(threshold_output, 'w') as f:
        json.dump({'threshold_20th_percentile': threshold_20th}, f)
    
    # Step 4: Calculate F1-max threshold
    threshold_f1_max = calculate_f1_max_threshold(train_df)
    with open(f1_output, 'w') as f:
        json.dump({'threshold_f1_max': threshold_f1_max}, f)
    
    # Step 5: Predict collapse
    test_df_loaded = pd.read_csv(str(test_output))
    predictions = predict_collapse(test_df_loaded, threshold_20th)
    
    # Step 6: Evaluate performance
    performance = evaluate_performance(test_df_loaded, predictions)
    
    # Step 7: Calculate correlation
    correlation = calculate_correlation(test_df_loaded)
    
    # Step 8: Null distribution
    null_dist = calculate_null_distribution(test_df_loaded, n_permutations=100, random_state=42)
    
    # Step 9: Power analysis
    power = calculate_power_analysis(train_df)
    
    # Step 10: Comparative report
    with open(threshold_output, 'r') as f:
        threshold_config = json.load(f)
    with open(f1_output, 'r') as f:
        f1_config = json.load(f)
    
    comparative = report_comparative_thresholds(
        threshold_config, f1_config, {}, {}
    )
    
    # Step 11: Generate final report
    final_report = generate_results_report(
        threshold_config,
        f1_config,
        predictions,
        performance,
        correlation,
        null_dist,
        {'baseline_mean_connectivity': baseline},
        {'linear_reasoning_index': 0.0, 'confirmed': False},
        {}, {},
        comparative,
        power
    )
    
    with open(results_output, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    # Verify all outputs exist
    assert train_output.exists()
    assert test_output.exists()
    assert baseline_output.exists()
    assert threshold_output.exists()
    assert f1_output.exists()
    assert results_output.exists()
    
    # Verify final report structure
    with open(results_output, 'r') as f:
        report = json.load(f)
    
    assert 'thresholds' in report
    assert 'performance' in report
    assert 'correlation' in report
    assert 'null_distribution' in report
    assert 'baseline' in report
    assert 'sensitivity' in report
    assert 'comparative_analysis' in report
    assert 'power_analysis' in report