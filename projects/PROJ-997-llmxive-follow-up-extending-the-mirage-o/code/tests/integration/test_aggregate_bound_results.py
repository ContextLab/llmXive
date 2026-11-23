"""
Integration test for T032: Aggregate bound results.
"""
import json
import tempfile
from pathlib import Path
import pytest
import logging

from src.cli.aggregate_bound_results import aggregate_results, write_report

@pytest.fixture
def mock_consistency_data():
    return {
        "per_level_correlations": {
            "INT4": 0.92,
            "INT8": 0.95,
            "FP8": 0.94
        },
        "global_consistency_metric": 0.9366666666666666,
        "bound_satisfaction_pct": 95.5
    }

def test_aggregate_results_pass(mock_consistency_data):
    """Test that a high global metric results in a PASS verdict."""
    result = aggregate_results(mock_consistency_data, threshold=0.90)
    assert result["verdict"] == "PASS"
    assert result["global_consistency_metric"] == mock_consistency_data["global_consistency_metric"]
    assert result["threshold"] == 0.90

def test_aggregate_results_fail(mock_consistency_data):
    """Test that a low global metric results in a FAIL verdict."""
    # Modify data to have a low metric
    low_data = mock_consistency_data.copy()
    low_data["global_consistency_metric"] = 0.85
    result = aggregate_results(low_data, threshold=0.90)
    assert result["verdict"] == "FAIL"

def test_write_report(tmp_path):
    """Test writing the report to a file."""
    report = {
        "global_consistency_metric": 0.95,
        "verdict": "PASS",
        "threshold": 0.90
    }
    output_file = tmp_path / "test_report.json"
    write_report(report, output_file)
    
    assert output_file.exists()
    with open(output_file, "r") as f:
        loaded = json.load(f)
    assert loaded["verdict"] == "PASS"
    assert loaded["global_consistency_metric"] == 0.95