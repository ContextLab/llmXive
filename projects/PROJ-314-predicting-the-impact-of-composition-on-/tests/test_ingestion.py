"""
Tests for ingestion module.
"""
import pytest
import pandas as pd
import json
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import generate_data_availability_report, validate_data_gap, MIN_DATA_THRESHOLD

def test_generate_data_availability_report_creates_file(tmp_path):
    """Test that generate_data_availability_report creates the JSON file."""
    # Mock DataFrame
    df = pd.DataFrame({
        "composition": ["Al2O3", "Si3N4"],
        "source": ["nist", "arxiv"]
    })
    
    # Temporarily override REPORTS_DIR for testing
    import ingestion
    original_reports_dir = ingestion.REPORTS_DIR
    test_reports_dir = tmp_path / "reports"
    test_reports_dir.mkdir(parents=True, exist_ok=True)
    ingestion.REPORTS_DIR = test_reports_dir
    
    try:
        generate_data_availability_report(df, 2)
        
        report_path = test_reports_dir / "data_availability_report.json"
        assert report_path.exists(), "Report file was not created."
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["status"] == "HALTED"
        assert report["actual_count"] == 2
        assert report["threshold"] == MIN_DATA_THRESHOLD
        assert "timestamp" in report
        assert len(report["recommendations"]) > 0
    finally:
        ingestion.REPORTS_DIR = original_reports_dir

def test_validate_data_gap_returns_false_when_below_threshold():
    """Test that validate_data_gap returns False when count < 30."""
    df = pd.DataFrame({
        "composition": ["Al2O3"] * 29,
        "source": ["nist"] * 29
    })
    assert not validate_data_gap(df)

def test_validate_data_gap_returns_true_when_above_threshold():
    """Test that validate_data_gap returns True when count >= 30."""
    df = pd.DataFrame({
        "composition": ["Al2O3"] * 30,
        "source": ["nist"] * 30
    })
    assert validate_data_gap(df)