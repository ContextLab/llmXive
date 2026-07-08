"""
Unit tests for the evaluation module (T029).

Tests verify that precision, recall, and F1 are calculated correctly
and that the module handles edge cases properly.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.audit.evaluation import (
    load_synthetic_summaries,
    load_ground_truth,
    load_audit_records,
    validate_summary,
    evaluate_detection,
    write_evaluation_results
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def synthetic_data(temp_dir):
    """Create a mock synthetic summaries file."""
    data = [
        {"id": "syn_001", "baseline_rate": 0.5, "variant_rate": 0.55, "sample_size": 1000, "ground_truth_inconsistent": False},
        {"id": "syn_002", "baseline_rate": 0.5, "variant_rate": 0.80, "sample_size": 1000, "ground_truth_inconsistent": True},
        {"id": "syn_003", "baseline_rate": 0.5, "variant_rate": 0.52, "sample_size": 1000, "ground_truth_inconsistent": False},
        {"id": "syn_004", "baseline_rate": 0.5, "variant_rate": 0.90, "sample_size": 1000, "ground_truth_inconsistent": True},
    ]
    path = temp_dir / "synthetic_summaries.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

@pytest.fixture
def ground_truth_data(temp_dir):
    """Create a mock ground truth file."""
    data = {
        "syn_001": {"is_inconsistent": False},
        "syn_002": {"is_inconsistent": True},
        "syn_003": {"is_inconsistent": False},
        "syn_004": {"is_inconsistent": True},
    }
    path = temp_dir / "ground_truth_labels.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

@pytest.fixture
def audit_records_data(temp_dir):
    """Create a mock audit records file with some inconsistencies."""
    # Perfect detection: syn_002 and syn_004 flagged, others not
    data = [
        {"summary_id": "syn_001", "is_inconsistent": False},
        {"summary_id": "syn_002", "is_inconsistent": True},
        {"summary_id": "syn_003", "is_inconsistent": False},
        {"summary_id": "syn_004", "is_inconsistent": True},
    ]
    path = temp_dir / "audit_report.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return path

def test_load_synthetic_summaries(synthetic_data):
    summaries = load_synthetic_summaries(synthetic_data)
    assert len(summaries) == 4
    assert "syn_001" in summaries
    assert summaries["syn_001"]["ground_truth_inconsistent"] is False

def test_load_ground_truth(ground_truth_data):
    gt = load_ground_truth(ground_truth_data)
    assert len(gt) == 4
    assert gt["syn_002"] is True
    assert gt["syn_001"] is False

def test_load_audit_records(audit_records_data):
    records = load_audit_records(audit_records_data)
    assert len(records) == 4
    assert records["syn_002"]["is_inconsistent"] is True

def test_validate_summary_perfect_detection(audit_records_data, ground_truth_data):
    """Test with perfect detection (TP=2, TN=2, FP=0, FN=0)."""
    ground_truth = load_ground_truth(ground_truth_data)
    audit_records = load_audit_records(audit_records_data)
    
    # Check syn_002 (True Positive)
    pred, actual = validate_summary("syn_002", ground_truth, audit_records)
    assert pred is True
    assert actual is True

    # Check syn_001 (True Negative)
    pred, actual = validate_summary("syn_001", ground_truth, audit_records)
    assert pred is False
    assert actual is False

def test_evaluate_detection_perfect(temp_dir, synthetic_data, ground_truth_data, audit_records_data):
    """Test evaluation with perfect detection."""
    metrics = evaluate_detection(synthetic_data, ground_truth_data, audit_records_data)
    
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0
    assert metrics['f1'] == 1.0
    assert metrics['true_positives'] == 2
    assert metrics['false_positives'] == 0
    assert metrics['false_negatives'] == 0
    assert metrics['true_negatives'] == 2

def test_evaluate_detection_with_errors(temp_dir, synthetic_data, ground_truth_data):
    """Test evaluation with false positives and false negatives."""
    # Create audit records with errors
    # syn_002: True Positive (correct)
    # syn_003: False Positive (flagged but actually consistent)
    # syn_004: False Negative (not flagged but actually inconsistent)
    data = [
        {"summary_id": "syn_001", "is_inconsistent": False},
        {"summary_id": "syn_002", "is_inconsistent": True},
        {"summary_id": "syn_003", "is_inconsistent": True},  # FP
        # syn_004 missing -> FN
    ]
    audit_path = temp_dir / "audit_report.json"
    with open(audit_path, 'w') as f:
        json.dump(data, f)
    
    metrics = evaluate_detection(synthetic_data, ground_truth_data, audit_path)
    
    # TP=1 (syn_002), FP=1 (syn_003), FN=1 (syn_004), TN=1 (syn_001)
    assert metrics['true_positives'] == 1
    assert metrics['false_positives'] == 1
    assert metrics['false_negatives'] == 1
    assert metrics['true_negatives'] == 1
    
    precision = 1 / (1 + 1)  # 0.5
    recall = 1 / (1 + 1)     # 0.5
    f1 = 2 * (0.5 * 0.5) / (0.5 + 0.5)  # 0.5
    
    assert abs(metrics['precision'] - precision) < 1e-6
    assert abs(metrics['recall'] - recall) < 1e-6
    assert abs(metrics['f1'] - f1) < 1e-6

def test_evaluate_detection_no_predictions(temp_dir, synthetic_data, ground_truth_data):
    """Test evaluation when no inconsistencies are predicted."""
    # No audit records or all False
    data = [
        {"summary_id": "syn_001", "is_inconsistent": False},
        {"summary_id": "syn_002", "is_inconsistent": False},
        {"summary_id": "syn_003", "is_inconsistent": False},
        {"summary_id": "syn_004", "is_inconsistent": False},
    ]
    audit_path = temp_dir / "audit_report.json"
    with open(audit_path, 'w') as f:
        json.dump(data, f)
    
    metrics = evaluate_detection(synthetic_data, ground_truth_data, audit_path)
    
    # TP=0, FP=0, FN=2, TN=2
    assert metrics['true_positives'] == 0
    assert metrics['false_positives'] == 0
    assert metrics['false_negatives'] == 2
    assert metrics['true_negatives'] == 2
    
    assert metrics['precision'] == 0.0  # Division by zero handled -> 0
    assert metrics['recall'] == 0.0
    assert metrics['f1'] == 0.0

def test_write_evaluation_results(temp_dir):
    """Test writing evaluation results to file."""
    results = {
        'precision': 0.95,
        'recall': 0.85,
        'f1': 0.89,
        'true_positives': 10,
        'false_positives': 1,
        'false_negatives': 2,
        'true_negatives': 87
    }
    output_path = temp_dir / "results.json"
    
    write_evaluation_results(results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved = json.load(f)
    
    assert saved['precision'] == 0.95
    assert saved['task_id'] == 'T029'
    assert 'timestamp' in saved
