import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
# Adjust import path if running from root vs code dir
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from generate_preprocessing_stats import load_subject_logs, calculate_stats

def test_calculate_stats_basic():
    """Test basic calculation of stats."""
    logs = [
        {"subject_id": "sub-01", "status": "success"},
        {"subject_id": "sub-02", "status": "success"},
        {"subject_id": "sub-03", "status": "failed", "error": "motion"},
        {"subject_id": "sub-04"}, # No status, assume success if no error
    ]
    
    stats = calculate_stats(logs, total_limit=10)
    
    assert stats["total_subjects"] == 10
    assert stats["successful_subjects"] == 3 # sub-01, sub-02, sub-04
    assert stats["success_rate_percentage"] == 30.0

def test_calculate_stats_empty():
    """Test stats calculation with no logs."""
    stats = calculate_stats([], total_limit=10)
    assert stats["total_subjects"] == 10
    assert stats["successful_subjects"] == 0
    assert stats["success_rate_percentage"] == 0.0

def test_calculate_stats_all_failed():
    """Test stats calculation when all fail."""
    logs = [
        {"subject_id": "sub-01", "status": "failed", "error": "motion"},
        {"subject_id": "sub-02", "status": "failed", "error": "missing_data"},
    ]
    stats = calculate_stats(logs, total_limit=5)
    assert stats["successful_subjects"] == 0
    assert stats["success_rate_percentage"] == 0.0

def test_load_subject_logs(tmp_path):
    """Test loading logs from a temporary directory."""
    log_dir = tmp_path / "processed"
    log_dir.mkdir()
    
    # Create dummy log files
    (log_dir / "sub-01_preprocess.log").write_text('{"subject_id": "sub-01", "status": "success"}')
    (log_dir / "sub-02_preprocess.log").write_text('{"subject_id": "sub-02", "status": "failed"}')
    
    logs = load_subject_logs(log_dir)
    assert len(logs) == 2
    
    ids = [l["subject_id"] for l in logs]
    assert "sub-01" in ids
    assert "sub-02" in ids

def test_load_subject_logs_no_dir():
    """Test loading from non-existent directory."""
    logs = load_subject_logs(Path("/nonexistent/path"))
    assert logs == []