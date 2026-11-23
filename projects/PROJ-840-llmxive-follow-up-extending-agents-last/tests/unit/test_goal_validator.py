"""
Unit tests for the Task Goal Validator module.
"""
import pytest
from code.classification.goal_validator import validate_static_constraints, process_traces

def test_extract_file_paths():
    description = "Please write to 'output.txt' and read from /tmp/data.csv"
    result = validate_static_constraints(description)
    assert "output.txt" in result["files"]
    assert "/tmp/data.csv" in result["files"]

def test_extract_variables():
    description = "Initialize var counter = 0 and let result = None"
    result = validate_static_constraints(description)
    assert "counter" in result["variables"]
    assert "result" in result["variables"]

def test_extract_functions():
    description = "Define def calculate_sum(a, b): and call it"
    result = validate_static_constraints(description)
    assert "calculate_sum" in result["functions"]

def test_extract_task_ids():
    description = "Complete task_123 and verify task_456"
    result = validate_static_constraints(description)
    assert "task_123" in result["task_ids"]
    assert "task_456" in result["task_ids"]

def test_extract_explicit_constraints():
    description = "Ensure file: report.pdf exists and var: status is set"
    result = validate_static_constraints(description)
    assert "file: report.pdf" in result["explicit_constraints"]
    assert "var: status" in result["explicit_constraints"]

def test_empty_description():
    result = validate_static_constraints("")
    assert result["files"] == []
    assert result["variables"] == []
    assert result["functions"] == []
    assert result["task_ids"] == []
    assert result["explicit_constraints"] == []

def test_process_traces():
    traces = [
        {
            "trace_id": "trace_001",
            "task_description": "Write to file 'log.txt' using var logger"
        },
        {
            "trace_id": "trace_002",
            "task_description": "Implement def process_data() for task_999"
        }
    ]
    results = process_traces(traces)
    
    assert "trace_001" in results
    assert "trace_002" in results
    assert "log.txt" in results["trace_001"]["constraints"]["files"]
    assert "logger" in results["trace_001"]["constraints"]["variables"]
    assert "process_data" in results["trace_002"]["constraints"]["functions"]
    assert "task_999" in results["trace_002"]["constraints"]["task_ids"]

def test_process_traces_missing_id():
    traces = [
        {
            "task_description": "Some task without ID"
        }
    ]
    results = process_traces(traces)
    assert len(results) == 0