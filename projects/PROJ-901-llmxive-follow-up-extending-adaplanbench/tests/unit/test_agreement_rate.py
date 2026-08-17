"""
Unit tests for T034: Agreement Rate Analysis.
"""
import os
import sys
import json
import csv
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.agreement_rate import (
    load_execution_traces,
    load_human_annotations,
    compute_agreement,
    compute_confidence_interval,
    run_agreement_analysis
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_execution_traces(temp_dir):
    """Test loading execution traces from CSV."""
    traces_path = os.path.join(temp_dir, "traces.csv")
    data = [
        {"task_id": "T1", "violation_boolean": "true", "violation_status": "violation"},
        {"task_id": "T2", "violation_boolean": "false", "violation_status": "no_violation"},
        {"task_id": "T3", "violation_boolean": "true", "violation_status": "implicit_unverified"},
    ]
    
    with open(traces_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    result = load_execution_traces(traces_path)
    assert len(result) == 3
    assert result[0]['task_id'] == 'T1'

def test_load_human_annotations(temp_dir):
    """Test loading human annotations."""
    ann_path = os.path.join(temp_dir, "labels.csv")
    data = [
        {"task_id": "T1", "is_violation": "true", "is_implicit": "false"},
        {"task_id": "T2", "is_violation": "false", "is_implicit": "false"},
        {"task_id": "T3", "is_violation": "true", "is_implicit": "true"},
    ]
    
    with open(ann_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    result = load_human_annotations(ann_path)
    assert len(result) == 3
    assert result['T1']['is_violation'] is True
    assert result['T2']['is_violation'] is False
    assert result['T3']['is_implicit'] is True

def test_compute_agreement_excludes_implicit(temp_dir):
    """Test that implicit_unverified rows are excluded."""
    traces = [
        {"task_id": "T1", "violation_boolean": "true", "violation_status": "violation"},
        {"task_id": "T2", "violation_boolean": "false", "violation_status": "no_violation"},
        {"task_id": "T3", "violation_boolean": "true", "violation_status": "implicit_unverified"}, # Should be excluded
    ]
    
    annotations = {
        "T1": {"is_violation": True, "is_implicit": False},
        "T2": {"is_violation": False, "is_implicit": False},
        "T3": {"is_violation": True, "is_implicit": True},
    }
    
    agreed, total = compute_agreement(traces, annotations)
    
    # T1 matches (true == true), T2 matches (false == false). T3 excluded.
    assert total == 2
    assert agreed == 2

def test_compute_agreement_mismatches(temp_dir):
    """Test mismatch detection."""
    traces = [
        {"task_id": "T1", "violation_boolean": "true", "violation_status": "violation"},
        {"task_id": "T2", "violation_boolean": "false", "violation_status": "no_violation"},
    ]
    
    annotations = {
        "T1": {"is_violation": False, "is_implicit": False}, # Mismatch
        "T2": {"is_violation": False, "is_implicit": False}, # Match
    }
    
    agreed, total = compute_agreement(traces, annotations)
    assert total == 2
    assert agreed == 1

def test_confidence_interval(temp_dir):
    """Test Wilson score interval calculation."""
    # Perfect agreement
    lower, upper = compute_confidence_interval(1.0, 10)
    assert lower >= 0.7 and upper == 1.0
    
    # Zero agreement
    lower, upper = compute_confidence_interval(0.0, 10)
    assert lower == 0.0 and upper <= 0.3

def test_run_agreement_analysis_integration(temp_dir):
    """Test full pipeline."""
    traces_path = os.path.join(temp_dir, "traces.csv")
    ann_path = os.path.join(temp_dir, "labels.csv")
    out_path = os.path.join(temp_dir, "report.json")
    
    # Prepare traces
    traces_data = [
        {"task_id": "T1", "violation_boolean": "true", "violation_status": "violation"},
        {"task_id": "T2", "violation_boolean": "false", "violation_status": "no_violation"},
        {"task_id": "T3", "violation_boolean": "true", "violation_status": "implicit_unverified"},
    ]
    with open(traces_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=traces_data[0].keys())
        writer.writeheader()
        writer.writerows(traces_data)
    
    # Prepare annotations
    ann_data = [
        {"task_id": "T1", "is_violation": "true", "is_implicit": "false"},
        {"task_id": "T2", "is_violation": "false", "is_implicit": "false"},
        {"task_id": "T3", "is_violation": "true", "is_implicit": "true"},
    ]
    with open(ann_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ann_data[0].keys())
        writer.writeheader()
        writer.writerows(ann_data)
    
    # Run
    result = run_agreement_analysis(traces_path, ann_path, out_path)
    
    # Verify file exists
    assert os.path.exists(out_path)
    
    # Verify content
    with open(out_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded['sample_size'] == 2
    assert loaded['agreed_count'] == 2
    assert abs(loaded['agreement_rate'] - 1.0) < 0.001
    assert 'confidence_interval_lower' in loaded
    assert 'confidence_interval_upper' in loaded