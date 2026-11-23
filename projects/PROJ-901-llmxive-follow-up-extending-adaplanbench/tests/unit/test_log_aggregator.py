"""
Unit tests for log_aggregator.py
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.log_aggregator import aggregate_logs, load_execution_logs, write_traces_csv

@pytest.fixture
def temp_files():
    """Create temporary files for testing."""
    temp_dir = tempfile.mkdtemp()
    mono_path = os.path.join(temp_dir, "monolithic_logs.json")
    dual_path = os.path.join(temp_dir, "dual_track_logs.json")
    output_path = os.path.join(temp_dir, "execution_traces.csv")
    
    # Create sample monolithic logs
    mono_data = [
        {
            "task_id": "task_001",
            "constraint_count": 5,
            "violation": True,
            "final_score": 0.5,
            "execution_time": 1.2
        },
        {
            "task_id": "task_002",
            "constraint_count": 6,
            "violation": False,
            "final_score": 1.0,
            "execution_time": 0.8
        }
    ]
    
    # Create sample dual-track logs
    dual_data = [
        {
            "task_id": "task_001",
            "constraint_count": 5,
            "violation": False,
            "final_score": 0.9,
            "execution_time": 1.5
        },
        {
            "task_id": "task_003",
            "constraint_count": 7,
            "violation": True,
            "final_score": 0.6,
            "execution_time": 2.1
        }
    ]
    
    with open(mono_path, 'w') as f:
        json.dump(mono_data, f)
    
    with open(dual_path, 'w') as f:
        json.dump(dual_data, f)
    
    yield mono_path, dual_path, output_path
    
    # Cleanup
    for p in [mono_path, dual_path, output_path]:
        if os.path.exists(p):
            os.remove(p)
    os.rmdir(temp_dir)

def test_load_execution_logs_list_format(temp_files):
    """Test loading logs in list format."""
    mono_path, _, _ = temp_files
    logs = load_execution_logs(mono_path)
    assert len(logs) == 2
    assert logs[0]['task_id'] == 'task_001'

def test_aggregate_logs_structure(temp_files):
    """Test that aggregate_logs produces correct structure."""
    mono_path, dual_path, _ = temp_files
    traces = aggregate_logs(mono_path, dual_path)
    
    assert len(traces) == 4  # 2 mono + 2 dual
    
    # Check first mono trace
    mono_trace = traces[0]
    assert mono_trace['architecture'] == 'monolithic'
    assert mono_trace['task_id'] == 'task_001'
    assert mono_trace['violation'] == True
    assert 'log_details' in mono_trace

    # Check first dual trace
    dual_trace = traces[2]
    assert dual_trace['architecture'] == 'dual_track'
    assert dual_trace['task_id'] == 'task_001'
    assert dual_trace['violation'] == False

def test_write_traces_csv(temp_files):
    """Test writing traces to CSV."""
    mono_path, dual_path, output_path = temp_files
    traces = aggregate_logs(mono_path, dual_path)
    write_traces_csv(traces, output_path)
    
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        lines = f.readlines()
    
    # Check header
    header = lines[0].strip().split(',')
    expected_headers = ['task_id', 'architecture', 'constraint_count', 
                      'violation', 'final_score', 'execution_time', 'log_details']
    assert header == expected_headers
    
    # Check row count (header + 4 data rows)
    assert len(lines) == 5

def test_aggregate_logs_empty(temp_files):
    """Test aggregation with empty logs."""
    mono_path, dual_path, _ = temp_files
    
    # Create empty files
    with open(mono_path, 'w') as f:
        json.dump([], f)
    with open(dual_path, 'w') as f:
        json.dump([], f)
    
    traces = aggregate_logs(mono_path, dual_path)
    assert len(traces) == 0

def test_aggregate_logs_missing_file(temp_files):
    """Test aggregation with missing file."""
    _, dual_path, _ = temp_files
    
    with pytest.raises(FileNotFoundError):
        aggregate_logs("/nonexistent/path.json", dual_path)