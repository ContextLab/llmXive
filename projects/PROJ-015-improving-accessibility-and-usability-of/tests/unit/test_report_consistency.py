"""
Unit tests for T113: Report Consistency Check.
"""
import pytest
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.report_consistency_check import (
    compute_file_checksum,
    verify_consistency,
    main
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def create_test_files(temp_dir):
    """Create test files for consistency checking."""
    # Create CSV files
    csv1 = temp_dir / "metrics_summary.csv"
    csv1.write_text("metric,value\ntime,100\nerrors,5\n")
    
    csv2 = temp_dir / "descriptive_stats.csv"
    csv2.write_text("stat,value\nmean,50\nstd,10\n")
    
    # Create report
    report = temp_dir / "report.txt"
    report.write_text("Summary report\n")
    
    # Create state file
    state_file = temp_dir / "state.json"
    
    return {
        "csv1": csv1,
        "csv2": csv2,
        "report": report,
        "state": state_file,
        "temp_dir": temp_dir
    }

def test_compute_file_checksum(temp_dir):
    """Test checksum computation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(test_file)
    assert checksum is not None
    assert len(checksum) == 64  # SHA-256 hex length
    
    # Verify checksum is correct
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected

def test_compute_file_checksum_missing_file(temp_dir):
    """Test checksum computation for missing file."""
    checksum = compute_file_checksum(temp_dir / "nonexistent.txt")
    assert checksum is None

def test_verify_consistency_initial_run(create_test_files):
    """Test consistency verification on initial run (no state file)."""
    files = create_test_files
    
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is True
    assert "Initial state created" in message
    
    # Verify state file was created
    assert files["state"].exists()
    
    # Verify state file content
    with open(files["state"]) as f:
        state = json.load(f)
    
    assert "csv_checksums" in state
    assert "report_checksum" in state
    assert len(state["csv_checksums"]) == 2

def test_verify_consistency_matching(create_test_files):
    """Test consistency verification when everything matches."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Second run should succeed
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is True
    assert "verified successfully" in message

def test_verify_consistency_csv_changed(create_test_files):
    """Test consistency verification when CSV content changes."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Change CSV content
    files["csv1"].write_text("metric,value\ntime,200\nerrors,10\n")
    
    # Second run should fail
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is False
    assert "has changed since report generation" in message

def test_verify_consistency_report_changed(create_test_files):
    """Test consistency verification when report content changes."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Change report content
    files["report"].write_text("Modified report\n")
    
    # Second run should fail
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is False
    assert "Report checksum mismatch" in message

def test_verify_consistency_missing_csv(create_test_files):
    """Test consistency verification when a CSV is missing."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Remove CSV
    files["csv1"].unlink()
    
    # Second run should fail
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is False
    assert "not found" in message

def test_verify_consistency_missing_report(create_test_files):
    """Test consistency verification when report is missing."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Remove report
    files["report"].unlink()
    
    # Second run should fail
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    assert success is False
    assert "not found" in message

def test_verify_consistency_new_csv(create_test_files):
    """Test consistency verification when a new CSV is added."""
    files = create_test_files
    
    # First run to create state
    verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"]],
        files["state"]
    )
    
    # Add new CSV
    new_csv = files["temp_dir"] / "new.csv"
    new_csv.write_text("new,data\n")
    
    # Second run should fail
    success, message = verify_consistency(
        files["report"],
        [files["csv1"], files["csv2"], new_csv],
        files["state"]
    )
    
    assert success is False
    assert "New CSV detected" in message

def test_main_success(temp_dir, capsys):
    """Test main function on success."""
    # Create files
    csv1 = temp_dir / "metrics_summary.csv"
    csv1.write_text("metric,value\ntime,100\n")
    
    report = temp_dir / "report.txt"
    report.write_text("Report\n")
    
    state = temp_dir / "state.json"
    
    # First run to create state
    with patch("sys.argv", [
        "report_consistency_check.py",
        "--report", str(report),
        "--csv", str(csv1),
        "--state", str(state)
    ]):
        main()
    
    captured = capsys.readouterr()
    assert "[SUCCESS]" in captured.out

def test_main_failure_missing_csv(temp_dir, capsys, capfd):
    """Test main function on failure (missing CSV)."""
    report = temp_dir / "report.txt"
    report.write_text("Report\n")
    
    state = temp_dir / "state.json"
    
    # First run to create state with missing CSV
    with patch("sys.argv", [
        "report_consistency_check.py",
        "--report", str(report),
        "--csv", str(temp_dir / "missing.csv"),
        "--state", str(state)
    ]):
        with pytest.raises(SystemExit) as excinfo:
            main()
    
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "[FAILURE]" in captured.err