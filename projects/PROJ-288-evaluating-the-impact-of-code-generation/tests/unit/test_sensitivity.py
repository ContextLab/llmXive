import pytest
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.sensitivity_analysis import (
    calculate_sensitivity_metrics,
    append_sensitivity_to_log,
    load_heuristic_scores_from_file
)

# Test data fixtures
SAMPLE_RECORDS = [
    {
        'pr_number': '101',
        'origin_label': 'Disclosing',
        'heuristic_score': 0.85,
        'lines_changed': 150
    },
    {
        'pr_number': '102',
        'origin_label': 'Non-Disclosing',
        'heuristic_score': 0.20,
        'lines_changed': 50
    },
    {
        'pr_number': '103',
        'origin_label': 'Disclosing',
        'heuristic_score': 0.45, # Borderline
        'lines_changed': 200
    },
    {
        'pr_number': '104',
        'origin_label': 'Non-Disclosing',
        'heuristic_score': 0.90, # False Positive candidate
        'lines_changed': 30
    }
]

def test_calculate_sensitivity_metrics_threshold_0():
    """At threshold 0.0, everything is predicted as positive."""
    thresholds = [0.0]
    metrics = calculate_sensitivity_metrics(SAMPLE_RECORDS, thresholds)
    
    assert len(metrics) == 1
    m = metrics[0]
    
    # Threshold 0.0 -> All predicted Disclosing (True)
    # Actual: 2 Disclosing, 2 Non-Disclosing
    # TP = 2, FP = 2, TN = 0, FN = 0
    assert m['true_positives'] == 2
    assert m['false_positives'] == 2
    assert m['true_negatives'] == 0
    assert m['false_negatives'] == 0
    assert m['precision'] == 0.5
    assert m['recall'] == 1.0
    assert m['error_rate'] == 0.5

def test_calculate_sensitivity_metrics_threshold_1():
    """At threshold 1.0, nothing is predicted as positive (assuming scores < 1.0)."""
    thresholds = [1.0]
    metrics = calculate_sensitivity_metrics(SAMPLE_RECORDS, thresholds)
    
    assert len(metrics) == 1
    m = metrics[0]
    
    # Threshold 1.0 -> All predicted Non-Disclosing (False)
    # TP = 0, FP = 0, TN = 2, FN = 2
    assert m['true_positives'] == 0
    assert m['false_positives'] == 0
    assert m['true_negatives'] == 2
    assert m['false_negatives'] == 2
    assert m['recall'] == 0.0
    assert m['error_rate'] == 0.5

def test_calculate_sensitivity_metrics_mid_threshold():
    """Test threshold 0.5."""
    # Scores: 0.85 (D), 0.20 (ND), 0.45 (D), 0.90 (ND)
    # Threshold 0.5:
    # 0.85 >= 0.5 -> Pred D (Actual D) -> TP
    # 0.20 < 0.5  -> Pred ND (Actual ND) -> TN
    # 0.45 < 0.5  -> Pred ND (Actual D) -> FN
    # 0.90 >= 0.5 -> Pred D (Actual ND) -> FP
    # TP=1, TN=1, FN=1, FP=1
    
    thresholds = [0.5]
    metrics = calculate_sensitivity_metrics(SAMPLE_RECORDS, thresholds)
    
    assert len(metrics) == 1
    m = metrics[0]
    assert m['true_positives'] == 1
    assert m['false_positives'] == 1
    assert m['true_negatives'] == 1
    assert m['false_negatives'] == 1
    assert m['precision'] == 0.5
    assert m['recall'] == 0.5
    assert m['f1_score'] == 0.5
    assert m['error_rate'] == 0.5

def test_append_sensitivity_to_log_creates_file(tmp_path):
    """Test that the function creates the log file if it doesn't exist."""
    log_path = tmp_path / "validation_log.csv"
    metrics = [{'threshold': 0.5, 'error_rate': 0.2}]
    
    append_sensitivity_to_log(metrics, str(log_path))
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['threshold'] == '0.5'
        assert rows[0]['error_rate'] == '0.2'

def test_append_sensitivity_to_log_appends(tmp_path):
    """Test that the function appends to existing file."""
    log_path = tmp_path / "validation_log.csv"
    
    # Create initial file
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threshold', 'error_rate'])
        writer.writeheader()
        writer.writerow({'threshold': '0.1', 'error_rate': '0.3'})
    
    metrics = [{'threshold': 0.5, 'error_rate': 0.2}]
    append_sensitivity_to_log(metrics, str(log_path))
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['threshold'] == '0.1'
        assert rows[1]['threshold'] == '0.5'

def test_load_heuristic_scores_from_file_missing():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_heuristic_scores_from_file("non_existent_file.csv")