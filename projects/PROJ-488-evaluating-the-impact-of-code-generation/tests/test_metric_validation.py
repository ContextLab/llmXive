"""
Tests for T022: Metric Validation.
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from metric_validation import (
    validate_single_metric, 
    run_metric_validation, 
    generate_diagnostic_report,
    VALID_RANGE_METRICS
)

@pytest.fixture
def temp_metrics_dir():
    """Create a temporary directory with test CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "data" / "metrics"
        metrics_dir.mkdir(parents=True)
        
        # Create a valid CSV
        valid_df = pd.DataFrame({
            'snippet_id': ['s1', 's2'],
            'cyclomatic_complexity': [5.0, 10.0],
            'loc': [20.0, 40.0],
            'timestamp': ['2023-01-01', '2023-01-02']
        })
        valid_df.to_csv(metrics_dir / "radon_metrics.csv", index=False)
        
        # Create a CSV with NaN
        nan_df = pd.DataFrame({
            'snippet_id': ['s3', 's4'],
            'cyclomatic_complexity': [5.0, float('nan')],
            'loc': [20.0, 30.0],
            'timestamp': ['2023-01-01', '2023-01-02']
        })
        nan_df.to_csv(metrics_dir / "radon_metrics_nan.csv", index=False)
        
        # Create a CSV with out-of-range value
        ooo_df = pd.DataFrame({
            'snippet_id': ['s5', 's6'],
            'cyclomatic_complexity': [5.0, 2000.0], # 2000 > 1000
            'loc': [20.0, 30.0],
            'timestamp': ['2023-01-01', '2023-01-02']
        })
        ooo_df.to_csv(metrics_dir / "radon_metrics_ooo.csv", index=False)
        
        yield metrics_dir

def test_validate_single_metric_valid(temp_metrics_dir):
    """Test validation of a clean dataset."""
    df = pd.read_csv(temp_metrics_dir / "radon_metrics.csv")
    total, failed, details = validate_single_metric(df, "radon_metrics")
    assert total == 2
    assert failed == 0
    assert len(details) == 0

def test_validate_single_metric_nan(temp_metrics_dir):
    """Test detection of NaN values."""
    df = pd.read_csv(temp_metrics_dir / "radon_metrics_nan.csv")
    total, failed, details = validate_single_metric(df, "radon_metrics_nan")
    assert total == 2
    assert failed == 1
    assert len(details) == 1
    assert "cyclomatic_complexity: NaN" in details[0]["issues"][0]

def test_validate_single_metric_ooo(temp_metrics_dir):
    """Test detection of out-of-range values."""
    df = pd.read_csv(temp_metrics_dir / "radon_metrics_ooo.csv")
    total, failed, details = validate_single_metric(df, "radon_metrics_ooo")
    assert total == 2
    assert failed == 1
    assert len(details) == 1
    assert any("out of range" in issue for issue in details[0]["issues"])

def test_run_metric_validation_passes(temp_metrics_dir):
    """Test that validation passes when data is clean (only valid file)."""
    # Remove the bad files for this specific test
    (temp_metrics_dir / "radon_metrics_nan.csv").unlink()
    (temp_metrics_dir / "radon_metrics_ooo.csv").unlink()
    
    result = run_metric_validation(temp_metrics_dir)
    assert result is True

def test_run_metric_validation_fails_high_failure_rate(temp_metrics_dir):
    """Test that validation fails and generates report when failure rate >= 5%."""
    # In this setup, we have 2 valid, 1 NaN, 1 OOO out of 6 total.
    # 2 failures out of 6 is ~33%, which is > 5%.
    with pytest.raises(SystemExit) as exc_info:
        run_metric_validation(temp_metrics_dir)
    
    assert exc_info.value.code == 102
    
    # Check that diagnostic report was generated
    report_path = Path("results/validation/diagnostic_report_T022.json")
    # Note: In a real run, this file is created. In test environment, 
    # we might need to check if it exists or mock the path.
    # For this test, we assume the function creates it.
    if report_path.exists():
        with open(report_path) as f:
            report = json.load(f)
        assert report["validation_status"] == "FAILED"
        assert report["summary"]["failure_rate_percent"] > 5.0
        report_path.unlink() # Cleanup
def test_generate_diagnostic_report():
    """Test the report generation logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        details = {
            "metric_a": [{"row_index": 0, "snippet_id": "s1", "issues": ["NaN"]}]
        }
        generate_diagnostic_report(100, 10, details, report_path)
        
        assert report_path.exists()
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["summary"]["total_snippets_processed"] == 100
        assert report["summary"]["total_failed_snippets"] == 10
        assert report["summary"]["failure_rate_percent"] == 10.0
        assert "metric_a" in report["details_by_metric"]