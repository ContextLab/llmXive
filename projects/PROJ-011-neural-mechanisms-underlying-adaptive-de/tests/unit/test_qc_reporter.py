"""
Unit tests for qc_reporter.py.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import from the module
from preprocessing.qc_reporter import (
    QCReportError,
    load_exclusion_data,
    calculate_exclusion_rate,
    assess_stability,
    generate_qc_summary
)
from utils.io import save_yaml

@pytest.fixture
def temp_exclusions_file():
    """Create a temporary exclusions file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "exclusions.yaml"
        data = {
            "total_attempted": 100,
            "excluded": [
                {"id": "sub-01", "reason": "motion"},
                {"id": "sub-02", "reason": "motion"},
                {"id": "sub-03", "reason": "missing_data"}
            ]
        }
        save_yaml(path, data)
        yield path

def test_load_exclusion_data_success(temp_exclusions_file):
    """Test successful loading of exclusions data."""
    data = load_exclusion_data(temp_exclusions_file)
    assert data["total_attempted"] == 100
    assert len(data["excluded"]) == 3

def test_load_exclusion_data_not_found():
    """Test loading from non-existent file raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nonexistent.yaml"
        with pytest.raises(QCReportError):
            load_exclusion_data(path)

def test_calculate_exclusion_rate():
    """Test exclusion rate calculation."""
    data = {"total_attempted": 100, "excluded": [{"id": "1"}, {"id": "2"}]}
    rate = calculate_exclusion_rate(data, 100)
    assert rate == 0.02

    # Edge case: zero total
    rate_zero = calculate_exclusion_rate(data, 0)
    assert rate_zero == 0.0

def test_assess_stability():
    """Test stability assessment."""
    data = {
        "excluded": [
            {"reason": "motion"},
            {"reason": "motion"},
            {"reason": "missing_data"}
        ]
    }
    metrics = assess_stability(data)
    assert metrics["total_excluded"] == 3
    assert metrics["reason_breakdown"]["motion"] == 2
    # 1 non-motion out of 3 -> stability 1 - (2/3) = 0.3333
    assert abs(metrics["stability_score"] - 0.3333) < 0.0001

def test_generate_qc_summary(temp_exclusions_file):
    """Test generation of the full QC summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "qc_summary.json"
        summary = generate_qc_summary(
            exclusions_path=temp_exclusions_file,
            output_path=output_path,
            threshold_volumes_percent=10.0,
            threshold_motion_mm=3.0
        )

        # Verify structure
        assert "total_participants" in summary
        assert "excluded_count" in summary
        assert "exclusion_rate" in summary
        assert summary["total_participants"] == 100
        assert summary["excluded_count"] == 3
        assert abs(summary["exclusion_rate"] - 0.03) < 0.001

        # Verify file written
        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == summary
