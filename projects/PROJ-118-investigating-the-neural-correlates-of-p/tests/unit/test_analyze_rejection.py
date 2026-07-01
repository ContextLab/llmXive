"""
Unit tests for the analyze_rejection module.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

# Import the module
import sys
import code
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from analyze_rejection import (
    parse_ica_log,
    find_ica_logs,
    analyze_rejection_rates,
    identify_excluded_participants,
    write_exclusion_log,
    REJECTION_THRESHOLD
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_parse_ica_log_success(temp_dir):
    """Test parsing a log file with valid rejection stats."""
    log_content = """
    Running ICA...
    Some processing...
    Rejected 15 epochs out of 100
    Final summary...
    """
    log_path = temp_dir / "test_ica.log"
    log_path.write_text(log_content)
    
    total, rejected = parse_ica_log(log_path)
    
    assert total == 100
    assert rejected == 15

def test_parse_ica_log_no_stats(temp_dir):
    """Test parsing a log file with no rejection stats."""
    log_content = """
    Running ICA...
    Some processing...
    No rejections mentioned here.
    """
    log_path = temp_dir / "test_ica.log"
    log_path.write_text(log_content)
    
    total, rejected = parse_ica_log(log_path)
    
    assert total == 0
    assert rejected == 0

def test_find_ica_logs(temp_dir):
    """Test finding ICA log files."""
    # Create dummy log files
    (temp_dir / "sub-01_ica.log").write_text("log")
    (temp_dir / "sub-02_ica.log").write_text("log")
    (temp_dir / "other_file.txt").write_text("text")
    
    logs = find_ica_logs(temp_dir)
    
    assert len(logs) == 2
    assert "01" in logs
    assert "02" in logs
    assert "other_file" not in logs

def test_analyze_rejection_rates(temp_dir):
    """Test calculating rejection rates."""
    # Create log files
    log1 = temp_dir / "sub-01_ica.log"
    log1.write_text("Rejected 10 epochs out of 100")
    
    log2 = temp_dir / "sub-02_ica.log"
    log2.write_text("Rejected 60 epochs out of 100")
    
    logs = find_ica_logs(temp_dir)
    results = analyze_rejection_rates(logs)
    
    assert results["01"]["rate"] == 0.10
    assert results["01"]["total"] == 100
    assert results["01"]["rejected"] == 10
    
    assert results["02"]["rate"] == 0.60
    assert results["02"]["total"] == 100
    assert results["02"]["rejected"] == 60

def test_identify_excluded_participants(temp_dir):
    """Test identifying participants above threshold."""
    results = {
        "01": {"total": 100, "rejected": 10, "rate": 0.10},
        "02": {"total": 100, "rejected": 60, "rate": 0.60},
        "03": {"total": 100, "rejected": 50, "rate": 0.50}, # Exactly threshold
        "04": {"total": 100, "rejected": 51, "rate": 0.51}, # Just above
    }
    
    excluded = identify_excluded_participants(results, threshold=0.50)
    
    assert "01" not in excluded
    assert "02" in excluded
    assert "03" not in excluded  # Exactly 50% is not > 50%
    assert "04" in excluded

def test_write_exclusion_log(temp_dir):
    """Test writing the exclusion log file."""
    excluded = {"02", "04"}
    output_path = temp_dir / "rejected_participants.log"
    
    write_exclusion_log(excluded, output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    
    assert "02" in content
    assert "04" in content
    assert "Total Excluded: 2" in content

def test_write_exclusion_log_empty(temp_dir):
    """Test writing empty exclusion log."""
    excluded = set()
    output_path = temp_dir / "rejected_participants.log"
    
    write_exclusion_log(excluded, output_path)
    
    content = output_path.read_text()
    assert "No participants excluded" in content

def test_integration_full_pipeline(temp_dir):
    """Test the full pipeline end-to-end."""
    # Create mock logs
    (temp_dir / "sub-01_ica.log").write_text("Rejected 10 epochs out of 100")
    (temp_dir / "sub-02_ica.log").write_text("Rejected 60 epochs out of 100")
    (temp_dir / "sub-03_ica.log").write_text("Rejected 50 epochs out of 100")
    
    from analyze_rejection import run_rejection_analysis
    
    result = run_rejection_analysis(temp_dir)
    
    assert "02" in result["excluded"]
    assert "01" not in result["excluded"]
    assert "03" not in result["excluded"]
    
    output_file = temp_dir / "rejected_participants.log"
    assert output_file.exists()