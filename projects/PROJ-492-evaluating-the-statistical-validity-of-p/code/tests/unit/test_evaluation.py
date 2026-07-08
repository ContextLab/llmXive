"""
Unit tests for the evaluation module (T029).
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Adjust import path based on actual project structure
from code.src.audit.evaluation import (
    load_synthetic_summaries,
    load_ground_truth,
    load_audit_records,
    evaluate_detection,
    PRECISION_THRESHOLD,
    RECALL_THRESHOLD
)

def test_load_synthetic_summaries_csv():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.csv"
        data = [
            {"record_id": "1", "is_inconsistent": "True", "other": "data"},
            {"record_id": "2", "is_inconsistent": "False", "other": "data"}
        ]
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        result = load_synthetic_summaries(path)
        assert len(result) == 2
        assert result[0]['is_inconsistent'] == "True"

def test_load_synthetic_summaries_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        data = [
            {"record_id": "1", "is_inconsistent": True},
            {"record_id": "2", "is_inconsistent": False}
        ]
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_synthetic_summaries(path)
        assert len(result) == 2
        assert result[0]['is_inconsistent'] is True

def test_load_ground_truth():
    summaries = [
        {"record_id": "1", "is_inconsistent": "True"},
        {"record_id": "2", "is_inconsistent": "False"},
        {"record_id": "3", "is_inconsistent": True}
    ]
    gt = load_ground_truth(summaries)
    assert gt["1"] is True
    assert gt["2"] is False
    assert gt["3"] is True

def test_evaluate_detection_perfect():
    ground_truth = {"1": True, "2": False}
    audit_records = [
        {"record_id": "1", "is_inconsistent": True},
        {"record_id": "2", "is_inconsistent": False}
    ]
    metrics = evaluate_detection(ground_truth, audit_records)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["tp"] == 1
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0

def test_evaluate_detection_missing_record():
    ground_truth = {"1": True, "2": False}
    # Record "1" is missing from audit records (predicted False)
    audit_records = [
        {"record_id": "2", "is_inconsistent": False}
    ]
    metrics = evaluate_detection(ground_truth, audit_records)
    # TP=0, FN=1 (actual True, predicted False), FP=0, TN=1
    assert metrics["precision"] == 0.0  # 0 / 0 -> 0.0 handled in func
    assert metrics["recall"] == 0.0
    assert metrics["fn"] == 1

def test_evaluate_detection_false_positive():
    ground_truth = {"1": False, "2": False}
    audit_records = [
        {"record_id": "1", "is_inconsistent": True}, # FP
        {"record_id": "2", "is_inconsistent": False}
    ]
    metrics = evaluate_detection(ground_truth, audit_records)
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 1.0 # No FN
    assert metrics["fp"] == 1

def test_thresholds_defined():
    assert PRECISION_THRESHOLD == 0.90
    assert RECALL_THRESHOLD == 0.80
