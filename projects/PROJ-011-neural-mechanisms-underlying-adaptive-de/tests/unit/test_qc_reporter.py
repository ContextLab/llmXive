"""
Unit tests for qc_reporter.py (T018b).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing.qc_reporter import (
    load_exclusion_data,
    calculate_exclusion_rate,
    assess_stability,
    generate_qc_summary,
    QCReportError
)
from utils.io import load_yaml, save_yaml

@pytest.fixture
def temp_exclusions_file(tmp_path):
    """Create a temporary state/exclusions.yaml for testing."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    exclusions_file = state_dir / "exclusions.yaml"
    
    # Create a realistic test dataset
    data = {
        "total_participants": 100,
        "participants": [f"sub-{i:03d}" for i in range(1, 101)],
        "excluded": [
            {"id": "sub-001", "reason": "motion_excess", "details": "15% volumes > 3mm"},
            {"id": "sub-005", "reason": "motion_excess", "details": "12% volumes > 3mm"},
            {"id": "sub-012", "reason": "missing_data", "details": "No NIfTI found"},
        ],
        "reasons": {
            "motion_excess": 2,
            "missing_data": 1
        }
    }
    
    with open(exclusions_file, 'w') as f:
        yaml.dump(data, f)
    
    return exclusions_file

def test_load_exclusion_data_success(temp_exclusions_file):
    """Test successful loading of exclusion data."""
    with patch('preprocessing.qc_reporter.EXCLUSIONS_FILE', temp_exclusions_file):
        data = load_exclusion_data()
        assert data["total_participants"] == 100
        assert len(data["excluded"]) == 3
        assert "motion_excess" in data["reasons"]

def test_load_exclusion_data_missing_file():
    """Test error handling for missing file."""
    with patch('preprocessing.qc_reporter.EXCLUSIONS_FILE', Path("/nonexistent/file.yaml")):
        with pytest.raises(QCReportError):
            load_exclusion_data()

def test_calculate_exclusion_rate():
    """Test calculation of exclusion rates."""
    data = {
        "total_participants": 50,
        "excluded": [1, 2, 3, 4, 5] # 10 excluded
    }
    
    rates = calculate_exclusion_rate(data)
    assert rates["total_participants"] == 50
    assert rates["excluded_participants"] == 5
    assert rates["exclusion_rate"] == 0.1
    assert rates["threshold_exceeded"] == False # 10% is not > 10% (strictly)
    
    # Test exceeded case
    data["excluded"].append(6) # 11 excluded
    rates = calculate_exclusion_rate(data)
    assert rates["exclusion_rate"] == 0.12
    assert rates["threshold_exceeded"] == True

def test_assess_stability():
    """Test stability assessment logic."""
    data = {
        "excluded": [
            {"reason": "motion"},
            {"reason": "motion"},
            {"reason": "motion"},
            {"reason": "noise"}
        ]
    }
    
    rates = {"excluded_participants": 4}
    stability = assess_stability(data, rates)
    
    assert stability["primary_exclusion_reason"] == "motion"
    assert stability["stability_score"] == 0.75 # 3/4
    assert stability["qc_threshold_compliance"] == "PASS"

def test_assess_stability_no_exclusions():
    """Test stability when no one is excluded."""
    data = {"excluded": []}
    rates = {"excluded_participants": 0}
    
    stability = assess_stability(data, rates)
    assert stability["stability_score"] == 1.0
    assert stability["primary_exclusion_reason"] == "none"

def test_generate_qc_summary_integration(temp_exclusions_file):
    """Integration test for the full summary generation."""
    with patch('preprocessing.qc_reporter.EXCLUSIONS_FILE', temp_exclusions_file):
        summary = generate_qc_summary()
        
        assert summary["report_type"] == "QC_Summary_SC001"
        assert "metrics" in summary
        assert "exclusion_rates" in summary["metrics"]
        assert "stability" in summary["metrics"]
        assert summary["metrics"]["exclusion_rates"]["exclusion_rate"] == 0.03 # 3/100

def test_main_execution(temp_exclusions_file, tmp_path):
    """Test the main entry point writes the file."""
    report_path = tmp_path / "data" / "reports" / "qc_summary.json"
    report_path.parent.mkdir(parents=True)
    
    with patch('preprocessing.qc_reporter.EXCLUSIONS_FILE', temp_exclusions_file):
        with patch('preprocessing.qc_reporter.QC_REPORT_FILE', report_path):
            with patch('preprocessing.qc_reporter.ensure_dir'):
                result = main()
                
    assert result == 0
    assert report_path.exists()
    
    with open(report_path) as f:
        content = json.load(f)
    assert content["status"] == "complete"