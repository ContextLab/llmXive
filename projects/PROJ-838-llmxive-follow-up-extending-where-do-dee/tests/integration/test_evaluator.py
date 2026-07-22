import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from evaluator import (
    load_metrics, save_metrics, stratified_split,
    calculate_baseline, calculate_20th_percentile_threshold,
    calculate_f1_max_threshold, predict_collapse, evaluate_performance,
    main
)

def test_full_pipeline(tmp_path):
    """
    Integration test for the full prediction pipeline on Train/Test split.
    Simulates the flow from T029 -> T030 -> T032 -> T033
    """
    # Setup paths
    metrics_csv = str(tmp_path / 'metrics.csv')
    train_csv = str(tmp_path / 'train_metrics.csv')
    test_csv = str(tmp_path / 'test_metrics.csv')
    threshold_json = str(tmp_path / 'threshold_config.json')
    predictions_csv = str(tmp_path / 'predictions.csv')
    performance_json = str(tmp_path / 'performance_report.json')

    # Create sample data
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

    # Write initial metrics
    with open(metrics_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    # 1. Load and Split (T029)
    loaded_data = load_metrics(metrics_csv)
    train_data, test_data = stratified_split(loaded_data, seed=42)
    save_metrics(train_data, train_csv)
    save_metrics(test_data, test_csv)

    assert os.path.exists(train_csv)
    assert os.path.exists(test_csv)

    # 2. Calculate 20th Percentile Threshold (T030)
    calculate_20th_percentile_threshold(train_data, threshold_json)
    assert os.path.exists(threshold_json)

    with open(threshold_json, 'r') as f:
        threshold_config = json.load(f)
    threshold = threshold_config['threshold_value']

    # 3. Predict Collapse (T032)
    predict_collapse(test_data, threshold, predictions_csv)
    assert os.path.exists(predictions_csv)

    # 4. Evaluate Performance (T033)
    evaluate_performance(test_data, predictions_csv, performance_json)
    assert os.path.exists(performance_json)

    # Verify performance metrics are reasonable
    with open(performance_json, 'r') as f:
        perf = json.load(f)

    assert 0.0 <= perf['precision'] <= 1.0
    assert 0.0 <= perf['recall'] <= 1.0
    assert 0.0 <= perf['f1_score'] <= 1.0
    assert perf['confusion_matrix']['true_positive'] >= 0
    assert perf['confusion_matrix']['false_positive'] >= 0
    assert perf['confusion_matrix']['true_negative'] >= 0
    assert perf['confusion_matrix']['false_negative'] >= 0

    # Verify total predictions match test set size
    total_preds = (
        perf['confusion_matrix']['true_positive'] +
        perf['confusion_matrix']['false_positive'] +
        perf['confusion_matrix']['true_negative'] +
        perf['confusion_matrix']['false_negative']
    )
    assert total_preds == len(test_data)
