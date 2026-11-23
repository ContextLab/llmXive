"""
Unit tests for logging_utils.py serialization functions.
"""
import pytest
import os
import json
import tempfile
import csv
from pathlib import Path
from src.logging_utils import (
    save_results_to_csv,
    save_results_to_json,
    serialize_entropy_results,
    serialize_convergence_results,
    log_exclusions
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_save_results_to_csv_empty_data(temp_dir):
    """Test that CSV is created with headers even if data is empty."""
    output_path = temp_dir / "test.csv"
    fieldnames = ['col1', 'col2']
    
    save_results_to_csv([], str(output_path), fieldnames)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == fieldnames

def test_save_results_to_csv_with_data(temp_dir):
    """Test CSV writing with actual data."""
    output_path = temp_dir / "test.csv"
    fieldnames = ['id', 'value']
    data = [
        {'id': 1, 'value': 'a'},
        {'id': 2, 'value': 'b'}
    ]
    
    save_results_to_csv(data, str(output_path), fieldnames)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['id'] == '1'
        assert rows[0]['value'] == 'a'

def test_save_results_to_json(temp_dir):
    """Test JSON writing."""
    output_path = temp_dir / "test.json"
    data = [{'key': 'value'}, {'key2': 'value2'}]
    
    save_results_to_json(data, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
        assert loaded == data

def test_serialize_entropy_results(temp_dir):
    """Test specific entropy serialization logic."""
    output_path = temp_dir / "entropy_results.csv"
    data = [
        {'task_id': '1', 'entropy': 0.5, 'cluster_count': 2, 'sample_count': 10, 'strata': 'easy', 'status': 'success'}
    ]
    
    serialize_entropy_results(data, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['task_id'] == '1'
        assert rows[0]['entropy'] == '0.5'
        assert 'status' in rows[0]

def test_serialize_convergence_results(temp_dir):
    """Test specific convergence serialization logic."""
    output_path = temp_dir / "convergence_results.csv"
    data = [
        {'task_id': '1', 'k': 2, 'converged': True, 'steps_to_converge': 1, 'solution_code': 'print(1)', 'strata': 'hard', 'execution_status': 'success'}
    ]
    
    serialize_convergence_results(data, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['k'] == '2'
        assert rows[0]['converged'] == 'True'

def test_log_exclusions(temp_dir):
    """Test exclusion logging."""
    output_path = temp_dir / "exclusions.json"
    data = [
        {'source': 'entropy', 'task_id': '1', 'reason': 'Zero entropy'}
    ]
    
    log_exclusions(data, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]['reason'] == 'Zero entropy'