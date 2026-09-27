import csv
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_spot_check import (
    load_annotations,
    calculate_false_negative_rate,
    handle_missing_annotations,
    save_validation_report
)

def test_load_annotations_valid():
    """Test loading a valid annotations CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("# Comment line\n")
        f.write("pr_id,is_ai_assisted\n")
        f.write("PR-001,1\n")
        f.write("PR-002,0\n")
        f.write("PR-003,1\n")
        temp_path = f.name

    try:
        data = load_annotations(Path(temp_path))
        assert len(data) == 3
        assert data[0]['pr_id'] == 'PR-001'
        assert data[0]['is_ai_assisted'] == '1'
        assert data[1]['is_ai_assisted'] == '0'
    finally:
        os.unlink(temp_path)

def test_calculate_false_negative_rate():
    """Test false negative calculation logic."""
    # Simulate annotations where model predicted 0 (non-AI) but human says 1 (AI)
    # These are False Negatives
    annotations = [
        {'pr_id': 'P1', 'is_ai_assisted': '1'}, # FN
        {'pr_id': 'P2', 'is_ai_assisted': '0'}, # TN
        {'pr_id': 'P3', 'is_ai_assisted': '1'}, # FN
        {'pr_id': 'P4', 'is_ai_assisted': '0'}, # TN
    ]
    
    processed_data = [] # Not strictly needed for this calc as we assume all sample is non-AI predicted
    
    result = calculate_false_negative_rate(annotations, processed_data)
    
    assert result['total_sample_size'] == 4
    assert result['false_negatives'] == 2
    assert result['false_negative_rate'] == 0.5
    assert result['status'] == 'VALIDATED'

def test_handle_missing_annotations():
    """Test handling of missing annotations file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "nonexistent.csv"
        report_path = Path(tmpdir) / "validation_report.csv"
        
        # Mock the save function to write to a known location
        # We will patch the internal logic or just check file creation
        # Since handle_missing_annotations creates the report directly
        
        result = handle_missing_annotations(missing_path)
        
        assert result is True
        assert report_path.exists()
        
        # Verify content
        with open(report_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 4
            # Check status
            status_row = next(r for r in rows if r['metric'] == 'status')
            assert status_row['value'] == 'UNVALIDATED'

def test_save_validation_report():
    """Test saving the validation report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.csv"
        data = {
            "total_sample_size": 10,
            "false_negatives": 1,
            "false_negative_rate": 0.1,
            "status": "VALIDATED"
        }
        
        save_validation_report(data, report_path)
        
        assert report_path.exists()
        with open(report_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 4
            rate_row = next(r for r in rows if r['metric'] == 'false_negative_rate')
            assert float(rate_row['value']) == 0.1