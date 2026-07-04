import json
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.audit.evaluation import (
    load_synthetic_summaries,
    load_ground_truth,
    evaluate_detection,
    validate_summary,
    main
)

@pytest.fixture
def synthetic_csv():
    return Path("data/synthetic/synthetic_validation.csv")

@pytest.fixture
def ground_truth_json():
    return Path("data/synthetic/synthetic_ground_truth.json")

@pytest.fixture
def audit_report_json():
    return Path("output/audit_report.json")

def test_load_synthetic_summaries_exists(synthetic_csv):
    """Test that synthetic validation CSV exists and can be loaded."""
    assert synthetic_csv.exists(), "synthetic_validation.csv must exist"
    records = load_synthetic_summaries(synthetic_csv)
    assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

def test_load_ground_truth_exists(ground_truth_json):
    """Test that ground truth JSON exists and can be loaded."""
    assert ground_truth_json.exists(), "synthetic_ground_truth.json must exist"
    records = load_ground_truth(ground_truth_json)
    assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

def test_evaluate_detection_computes_metrics(synthetic_csv, ground_truth_json, audit_report_json):
    """Test that evaluation computes precision, recall, and F1."""
    synthetic_summaries = load_synthetic_summaries(synthetic_csv)
    ground_truth = load_ground_truth(ground_truth_json)
    
    # Create mock audit records for testing
    audit_records = []
    for i, rec in enumerate(ground_truth[:1000]):
        audit_records.append({
            'id': rec.get('id'),
            'is_inconsistent': rec.get('is_inconsistent', False)
        })
    
    metrics = evaluate_detection(audit_records, ground_truth)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert 'true_positives' in metrics
    assert 'false_positives' in metrics
    assert 'true_negatives' in metrics
    assert 'false_negatives' in metrics

def test_validate_summary_thresholds():
    """Test validation against thresholds."""
    thresholds = {'precision': 0.90, 'recall': 0.80, 'f1': 0.85}
    
    # Test passing case
    passing_metrics = {'precision': 0.92, 'recall': 0.85, 'f1': 0.88}
    passed, failures = validate_summary(passing_metrics, thresholds)
    assert passed, "Passing metrics should not fail"
    assert len(failures) == 0
    
    # Test failing precision
    failing_precision = {'precision': 0.85, 'recall': 0.85, 'f1': 0.85}
    passed, failures = validate_summary(failing_precision, thresholds)
    assert not passed, "Low precision should fail"
    assert any('Precision' in f for f in failures)

def test_full_evaluation_workflow(synthetic_csv, ground_truth_json, audit_report_json):
    """Test the full evaluation workflow if all files exist."""
    if not (synthetic_csv.exists() and ground_truth_json.exists() and audit_report_json.exists()):
        pytest.skip("Required files not present for full workflow test")
    
    # This would normally run the main() function
    # For now, we just verify the components work together
    synthetic_summaries = load_synthetic_summaries(synthetic_csv)
    ground_truth = load_ground_truth(ground_truth_json)
    
    # Load actual audit report
    with open(audit_report_json, 'r') as f:
        audit_data = json.load(f)
    audit_records = audit_data.get('records', [])
    
    metrics = evaluate_detection(audit_records, ground_truth)
    
    thresholds = {'precision': 0.90, 'recall': 0.80, 'f1': 0.85}
    passed, failures = validate_summary(metrics, thresholds)
    
    if not passed:
        pytest.fail(f"Evaluation failed: {failures}")
    
    assert passed, "Evaluation must pass thresholds"
    assert metrics['precision'] >= 0.90
    assert metrics['recall'] >= 0.80
    assert metrics['f1'] >= 0.85