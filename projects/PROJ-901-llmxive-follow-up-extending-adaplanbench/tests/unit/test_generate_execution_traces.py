"""
Unit tests for generate_execution_traces.py (T024)
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.generate_execution_traces import (
    load_execution_logs,
    load_filtered_tasks_map,
    extract_trace_data,
    write_traces_csv
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_execution_logs_valid_json(temp_dir):
    """Test loading valid JSON logs."""
    log_file = temp_dir / "test_logs.json"
    test_data = [
        {"task_id": "1", "violation_boolean": True, "final_score": 0.9},
        {"task_id": "2", "violation_boolean": False, "final_score": 0.8}
    ]
    
    with open(log_file, 'w') as f:
        json.dump(test_data, f)
    
    logs = load_execution_logs(log_file)
    
    assert len(logs) == 2
    assert logs[0]["task_id"] == "1"
    assert logs[1]["violation_boolean"] is False

def test_load_filtered_tasks_map(temp_dir):
    """Test loading filtered tasks and creating task map."""
    csv_file = temp_dir / "filtered_tasks.csv"
    test_data = [
        {"task_id": "1", "constraint_count": "5", "raw_prompt": "test1"},
        {"task_id": "2", "constraint_count": "7", "raw_prompt": "test2"}
    ]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "constraint_count", "raw_prompt"])
        writer.writeheader()
        writer.writerows(test_data)
    
    task_map = load_filtered_tasks_map(csv_file)
    
    assert "1" in task_map
    assert task_map["1"]["constraint_count"] == 5
    assert task_map["2"]["constraint_count"] == 7

def test_extract_trace_data(temp_dir):
    """Test extracting trace data from a log entry."""
    # Create task map
    csv_file = temp_dir / "filtered_tasks.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "constraint_count"])
        writer.writeheader()
        writer.writerow({"task_id": "1", "constraint_count": "5"})
    
    task_map = load_filtered_tasks_map(csv_file)
    
    log_entry = {
        "task_id": "1",
        "violation_boolean": True,
        "violation_reason": "Test violation",
        "final_score": 0.75
    }
    
    trace = extract_trace_data(log_entry, task_map, "dual_track")
    
    assert trace["task_id"] == "1"
    assert trace["architecture"] == "dual_track"
    assert trace["constraint_count"] == 5
    assert trace["violation_boolean"] is True
    assert trace["violation_reason"] == "Test violation"
    assert trace["final_score"] == 0.75

def test_write_traces_csv(temp_dir):
    """Test writing traces to CSV."""
    traces = [
        {
            "task_id": "1",
            "architecture": "dual_track",
            "constraint_count": 5,
            "violation_boolean": True,
            "violation_reason": "Test",
            "final_score": 0.75
        }
    ]
    
    output_file = temp_dir / "output.csv"
    write_traces_csv(traces, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["task_id"] == "1"
    assert rows[0]["architecture"] == "dual_track"
    assert rows[0]["constraint_count"] == "5"