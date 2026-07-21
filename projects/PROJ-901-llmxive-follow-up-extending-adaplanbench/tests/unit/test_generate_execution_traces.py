"""
Unit tests for generate_execution_traces.py
"""
import pytest
import json
import csv
import os
from pathlib import Path
import tempfile
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.analysis.generate_execution_traces import (
    load_execution_logs,
    load_filtered_tasks_map,
    extract_trace_data,
    write_traces_csv
)


class TestLoadExecutionLogs:
    def test_load_list_logs(self, tmp_path):
        """Test loading a JSON file that is a list of logs."""
        log_file = tmp_path / "logs.json"
        data = [{"task_id": "1", "score": 0.5}, {"task_id": "2", "score": 0.8}]
        with open(log_file, 'w') as f:
            json.dump(data, f)
        
        result = load_execution_logs(log_file)
        assert len(result) == 2
        assert result[0]["task_id"] == "1"

    def test_load_dict_with_results(self, tmp_path):
        """Test loading a JSON file with a 'results' key."""
        log_file = tmp_path / "logs.json"
        data = {"results": [{"task_id": "1", "score": 0.5}]}
        with open(log_file, 'w') as f:
            json.dump(data, f)
        
        result = load_execution_logs(log_file)
        assert len(result) == 1
        assert result[0]["task_id"] == "1"

    def test_missing_file(self, tmp_path):
        """Test handling of missing file."""
        with pytest.raises(FileNotFoundError):
            load_execution_logs(tmp_path / "nonexistent.json")


class TestLoadFilteredTasksMap:
    def test_load_csv_map(self, tmp_path):
        """Test loading a CSV and creating a task map."""
        csv_file = tmp_path / "tasks.csv"
        content = "task_id,constraint_count\ntask_1,[1,2,3]\ntask_2,5"
        with open(csv_file, 'w') as f:
            f.write(content)
        
        task_map = load_filtered_tasks_map(csv_file)
        assert "task_1" in task_map
        assert task_map["task_1"]["constraint_count"] == 3
        assert task_map["task_2"]["constraint_count"] == 5

    def test_missing_file(self, tmp_path):
        """Test handling of missing CSV file."""
        with pytest.raises(FileNotFoundError):
            load_filtered_tasks_map(tmp_path / "nonexistent.csv")


class TestExtractTraceData:
    def test_extract_with_violations(self, tmp_path):
        """Test extraction when violations exist."""
        log_entry = {
            "task_id": "t1",
            "violations": [{"type": "explicit", "desc": "bad"}],
            "final_score": 0.4
        }
        tasks_map = {"t1": {"constraint_count": 5}}
        
        trace = extract_trace_data(log_entry, tasks_map, "monolithic")
        assert trace["task_id"] == "t1"
        assert trace["architecture"] == "monolithic"
        assert trace["constraint_count"] == 5
        assert trace["violation"] is True
        assert trace["final_score"] == 0.4

    def test_extract_without_violations(self, tmp_path):
        """Test extraction when no violations exist."""
        log_entry = {
            "task_id": "t2",
            "violations": [],
            "final_score": 1.0
        }
        tasks_map = {"t2": {"constraint_count": 3}}
        
        trace = extract_trace_data(log_entry, tasks_map, "dual_track")
        assert trace["violation"] is False
        assert trace["final_score"] == 1.0

    def test_extract_missing_task_id(self, tmp_path):
        """Test extraction when task_id is missing."""
        log_entry = {"violations": [], "final_score": 1.0}
        tasks_map = {}
        
        trace = extract_trace_data(log_entry, tasks_map, "monolithic")
        assert trace is None


class TestWriteTracesCsv:
    def test_write_csv(self, tmp_path):
        """Test writing traces to CSV."""
        traces = [
            {"task_id": "1", "architecture": "m", "constraint_count": 5, "violation": True, "final_score": 0.5},
            {"task_id": "2", "architecture": "d", "constraint_count": 3, "violation": False, "final_score": 1.0}
        ]
        output_file = tmp_path / "traces.csv"
        
        write_traces_csv(traces, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["violation"] == "True" # CSV writes booleans as strings
            assert rows[0]["final_score"] == "0.5"

    def test_write_empty(self, tmp_path):
        """Test writing empty traces list."""
        output_file = tmp_path / "traces_empty.csv"
        write_traces_csv([], output_file)
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ['task_id', 'architecture', 'constraint_count', 'violation', 'final_score']