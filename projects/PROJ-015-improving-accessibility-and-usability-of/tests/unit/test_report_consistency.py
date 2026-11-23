import pytest
import os
import json
import tempfile
from pathlib import Path
import hashlib

# Import the functions we are testing
from code.analysis.report_consistency_check import (
    compute_file_checksum,
    verify_consistency,
    get_expected_checksums
)

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_checksum(temp_dir):
    """Test that checksum is computed correctly and is deterministic."""
    file_path = temp_dir / "test.txt"
    content = "Hello, World!"
    file_path.write_text(content)
    
    checksum = compute_file_checksum(file_path)
    expected = compute_sha256(content)
    
    assert checksum == expected
    assert len(checksum) == 64  # SHA-256 hex length

def test_compute_file_checksum_missing_file():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("nonexistent_file.txt"))

def test_verify_consistency_missing_report(temp_dir):
    """Test that verification fails if report is missing."""
    metrics = temp_dir / "metrics_summary.csv"
    metrics.write_text("metric,F_stat,p_val\ntest,1.0,0.5")
    
    descriptive = temp_dir / "descriptive_stats.csv"
    descriptive.write_text("stat,value\nmean,1.0")
    
    report = temp_dir / "report_summary.txt"
    
    is_consistent, message = verify_consistency(report, metrics, descriptive)
    
    assert not is_consistent
    assert "Missing required file: report_summary.txt" in message

def test_verify_consistency_success(temp_dir):
    """Test that verification passes when all files exist and are valid."""
    report = temp_dir / "report_summary.txt"
    report.write_text("Analysis Report\nF-stat: 1.0\np-value: 0.5\nANOVA results included.")
    
    metrics = temp_dir / "metrics_summary.csv"
    metrics.write_text("metric,F_stat,p_val\ntest,1.0,0.5")
    
    descriptive = temp_dir / "descriptive_stats.csv"
    descriptive.write_text("stat,value\nmean,1.0")
    
    is_consistent, message = verify_consistency(report, metrics, descriptive)
    
    assert is_consistent
    assert "Consistent" in message

def test_verify_consistency_checksum_mismatch(temp_dir):
    """Test that verification fails if checksums don't match expected."""
    report = temp_dir / "report_summary.txt"
    report.write_text("Report Content A")
    
    metrics = temp_dir / "metrics_summary.csv"
    metrics.write_text("data")
    
    descriptive = temp_dir / "descriptive_stats.csv"
    descriptive.write_text("data")
    
    # Create expected checksums that DO NOT match the current files
    wrong_checksums = {
        "report_summary.txt": "0000000000000000000000000000000000000000000000000000000000000000",
        "metrics_summary.csv": "1111111111111111111111111111111111111111111111111111111111111111",
        "descriptive_stats_explanation_engagement.csv": "2222222222222222222222222222222222222222222222222222222222222222"
    }
    
    is_consistent, message = verify_consistency(
        report, metrics, descriptive, expected_checksums=wrong_checksums
    )
    
    assert not is_consistent
    assert "Checksum mismatch" in message

def test_verify_consistency_empty_report(temp_dir):
    """Test that verification fails if report is empty."""
    report = temp_dir / "report_summary.txt"
    report.write_text("")  # Empty file
    
    metrics = temp_dir / "metrics_summary.csv"
    metrics.write_text("data")
    
    descriptive = temp_dir / "descriptive_stats.csv"
    descriptive.write_text("data")
    
    is_consistent, message = verify_consistency(report, metrics, descriptive)
    
    assert not is_consistent
    assert "report_summary.txt is empty" in message
