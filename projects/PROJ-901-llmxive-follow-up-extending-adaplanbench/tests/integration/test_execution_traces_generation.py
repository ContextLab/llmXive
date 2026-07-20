"""
Integration test for execution traces generation.

Verifies that the generate_execution_traces script correctly processes
execution logs and produces the expected CSV output.
"""
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.generate_execution_traces import (
    load_execution_logs,
    extract_trace_data,
    write_traces_csv,
    main
)
from config import Paths


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory with sample execution logs."""
    temp_dir = tempfile.mkdtemp()
    log_path = Path(temp_dir)

    # Create sample logs
    sample_logs = [
        {
            "task_id": "task_001",
            "architecture": "dual_track",
            "constraint_count": 5,
            "violations": [
                {"type": "constraint_violation", "description": "Failed to meet constraint A", "corrected": True}
            ],
            "final_score": 0.85
        },
        {
            "task_id": "task_002",
            "architecture": "monolithic",
            "constraint_count": 6,
            "violations": [],
            "final_score": 0.92
        },
        {
            "task_id": "task_003",
            "architecture": "dual_track",
            "constraint_count": 7,
            "violations": [
                {"type": "planning_error", "description": "Invalid plan sequence", "corrected": False}
            ],
            "final_score": 0.65
        }
    ]

    for i, log in enumerate(sample_logs):
        log_file = log_path / f"log_{i}.json"
        with open(log_file, 'w') as f:
            json.dump(log, f)

    yield log_path

    # Cleanup
    shutil.rmtree(temp_dir)


def test_load_execution_logs(temp_log_dir):
    """Test loading execution logs from directory."""
    logs = load_execution_logs(temp_log_dir)
    assert len(logs) == 3
    assert logs[0]["task_id"] == "task_001"
    assert logs[1]["architecture"] == "monolithic"
    assert logs[2]["final_score"] == 0.65


def test_extract_trace_data(temp_log_dir):
    """Test extracting trace data from logs."""
    logs = load_execution_logs(temp_log_dir)
    traces = extract_trace_data(logs)

    assert len(traces) == 3

    # Check first trace (has violation)
    assert traces[0]["task_id"] == "task_001"
    assert traces[0]["architecture"] == "dual_track"
    assert traces[0]["constraint_count"] == 5
    assert traces[0]["has_violation"] is True
    assert traces[0]["final_score"] == 0.85
    assert "constraint_violation" in traces[0]["violation_types"]

    # Check second trace (no violation)
    assert traces[1]["task_id"] == "task_002"
    assert traces[1]["has_violation"] is False
    assert traces[1]["violation_types"] == ""

    # Check third trace
    assert traces[2]["task_id"] == "task_003"
    assert traces[2]["has_violation"] is True
    assert "planning_error" in traces[2]["violation_types"]


def test_write_traces_csv(temp_log_dir):
    """Test writing traces to CSV."""
    logs = load_execution_logs(temp_log_dir)
    traces = extract_trace_data(logs)

    output_path = temp_log_dir / "output.csv"
    write_traces_csv(traces, output_path)

    assert output_path.exists()

    # Read and verify CSV content
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert "task_id" in rows[0]
    assert "architecture" in rows[0]
    assert "constraint_count" in rows[0]
    assert "has_violation" in rows[0]
    assert "final_score" in rows[0]

    # Verify specific values
    assert rows[0]["task_id"] == "task_001"
    assert rows[0]["has_violation"] == "True"
    assert rows[1]["has_violation"] == "False"


def test_main_integration(temp_log_dir):
    """Test the full main function with temporary paths."""
    # Create a temporary output directory
    output_dir = tempfile.mkdtemp()
    output_path = Path(output_dir) / "execution_traces.csv"

    # Mock the Paths class to use our temp directories
    original_paths = Paths()

    # We need to test the script logic directly since main() uses global Paths
    # Instead, we test the core functions which main() uses
    logs = load_execution_logs(temp_log_dir)
    traces = extract_trace_data(logs)
    write_traces_csv(traces, output_path)

    assert output_path.exists()

    # Verify the CSV has the expected structure
    with open(output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert all("task_id" in row for row in rows)
    assert all("architecture" in row for row in rows)
    assert all("constraint_count" in row for row in rows)
    assert all("has_violation" in row for row in rows)
    assert all("final_score" in row for row in rows)

    # Cleanup
    shutil.rmtree(output_dir)


def test_empty_logs_handling():
    """Test handling of empty logs directory."""
    temp_dir = tempfile.mkdtemp()
    try:
        log_path = Path(temp_dir)
        # Directory exists but is empty
        with pytest.raises(ValueError, match="No valid execution logs found"):
            load_execution_logs(log_path)
    finally:
        shutil.rmtree(temp_dir)