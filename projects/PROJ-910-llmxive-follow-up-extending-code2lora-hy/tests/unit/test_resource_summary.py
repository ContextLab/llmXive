"""
Unit tests for code/utils/resource_summary.py (T050).
"""
import os
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Adjust import path for testing context if needed, but assuming standard project structure
from utils.resource_summary import (
    load_memory_logs,
    compute_stage_stats,
    compute_runtime_from_logs,
    write_summary_csv,
    verify_constraints,
    ensure_results_dir,
    RESULTS_DIR,
    SUMMARY_PATH
)

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary results directory."""
    # We need to mock the global RESULTS_DIR to point to tmp_path
    # Since the module uses a global constant, we patch it
    with patch("utils.resource_summary.RESULTS_DIR", tmp_path):
        yield tmp_path

@pytest.fixture
def mock_memory_logs():
    """Provide sample memory log data."""
    return [
        {"stage": "generate", "timestamp": "2023-01-01 10:00:00", "memory_mb": 1000.0, "peak_mb": 1500.0},
        {"stage": "generate", "timestamp": "2023-01-01 10:05:00", "memory_mb": 1200.0, "peak_mb": 1600.0},
        {"stage": "evaluate", "timestamp": "2023-01-01 10:10:00", "memory_mb": 2000.0, "peak_mb": 2500.0},
        {"stage": "evaluate", "timestamp": "2023-01-01 10:15:00", "memory_mb": 1800.0, "peak_mb": 2200.0},
    ]

def test_ensure_results_dir(temp_results_dir):
    """Test that ensure_results_dir creates the directory."""
    # The function should create the directory if it doesn't exist
    # Since we patched RESULTS_DIR to temp_results_dir, and tmp_path exists,
    # this just verifies no exception is raised.
    result = ensure_results_dir()
    assert result.exists()
    assert result == temp_results_dir

def test_load_memory_logs_empty(temp_results_dir):
    """Test loading from non-existent file returns empty list."""
    # Ensure the file doesn't exist
    log_path = temp_results_dir / "memory_log.csv"
    if log_path.exists():
        log_path.unlink()
    
    logs = load_memory_logs()
    assert logs == []

def test_load_memory_logs_valid(temp_results_dir, mock_memory_logs):
    """Test loading valid CSV data."""
    log_path = temp_results_dir / "memory_log.csv"
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=mock_memory_logs[0].keys())
        writer.writeheader()
        writer.writerows(mock_memory_logs)
    
    logs = load_memory_logs()
    assert len(logs) == 4
    assert logs[0]["stage"] == "generate"
    assert logs[0]["peak_mb"] == 1500.0

def test_compute_stage_stats(mock_memory_logs):
    """Test stage statistics computation."""
    stats = compute_stage_stats(mock_memory_logs)
    
    assert "generate" in stats
    assert "evaluate" in stats
    
    # Generate: peaks 1500, 1600 -> max 1600
    assert stats["generate"]["peak_mb"] == 1600.0
    assert stats["generate"]["count"] == 2
    
    # Evaluate: peaks 2500, 2200 -> max 2500
    assert stats["evaluate"]["peak_mb"] == 2500.0
    assert stats["evaluate"]["count"] == 2

def test_compute_runtime_from_logs(mock_memory_logs):
    """Test runtime computation from timestamps."""
    runtime = compute_runtime_from_logs(mock_memory_logs)
    # 10:00:00 to 10:15:00 is 15 minutes = 900 seconds
    assert runtime == 900.0

def test_verify_constraints_pass():
    """Test constraint verification with valid values."""
    # 5 GB < 7 GB, 4 hours < 6 hours
    assert verify_constraints(5 * 1024, 4 * 3600) is True

def test_verify_constraints_fail_ram():
    """Test constraint verification failing on RAM."""
    # 8 GB > 7 GB
    assert verify_constraints(8 * 1024, 4 * 3600) is False

def test_verify_constraints_fail_time():
    """Test constraint verification failing on time."""
    # 5 GB < 7 GB, but 7 hours > 6 hours
    assert verify_constraints(5 * 1024, 7 * 3600) is False

def test_write_summary_csv(temp_results_dir, mock_memory_logs):
    """Test writing the summary CSV file."""
    # Setup logs
    log_path = temp_results_dir / "memory_log.csv"
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=mock_memory_logs[0].keys())
        writer.writeheader()
        writer.writerows(mock_memory_logs)
    
    # Compute stats
    stats = compute_stage_stats(load_memory_logs())
    runtime = compute_runtime_from_logs(load_memory_logs())
    peak = max(log.get("peak_mb", 0) for log in load_memory_logs())
    
    # Write
    write_summary_csv(stats, runtime, peak)
    
    # Verify file exists
    assert SUMMARY_PATH.exists()
    
    # Verify content
    with open(SUMMARY_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check for global metrics
    metrics = [r["metric"] for r in rows]
    assert "peak_ram_gb" in metrics
    assert "total_runtime_hours" in metrics
    
    # Check values
    peak_row = next(r for r in rows if r["metric"] == "peak_ram_gb")
    assert float(peak_row["value"]) > 0
    assert peak_row["status"] == "PASS" # 2.5GB < 7GB
    
    time_row = next(r for r in rows if r["metric"] == "total_runtime_hours")
    assert float(time_row["value"]) > 0
    assert time_row["status"] == "PASS" # 0.25h < 6h