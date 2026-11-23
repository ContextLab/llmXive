import pytest
import os
import json
import csv
from pathlib import Path
from unittest.mock import mock_open, patch
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from save_processed_data import load_raw_pr_data, load_repo_metadata, save_processed_data

def test_load_raw_pr_data_exists():
    """Test that load_raw_pr_data raises FileNotFoundError if file is missing."""
    with pytest.raises(FileNotFoundError):
        load_raw_pr_data(Path('nonexistent/file.json'))

def test_load_raw_pr_data_success(tmp_path):
    """Test that load_raw_pr_data successfully loads a JSON file."""
    test_file = tmp_path / "test.json"
    test_data = [{"pr_id": "1", "repo_name": "test"}]
    test_file.write_text(json.dumps(test_data))
    
    result = load_raw_pr_data(test_file)
    assert result == test_data

def test_load_repo_metadata_missing(tmp_path):
    """Test that load_repo_metadata returns empty dict if file is missing."""
    result = load_repo_metadata(tmp_path / "missing.json")
    assert result == {}

def test_load_repo_metadata_success(tmp_path):
    """Test that load_repo_metadata loads a JSON file."""
    test_file = tmp_path / "meta.json"
    test_data = {"repo_name": "test", "stars": 100}
    test_file.write_text(json.dumps(test_data))
    
    result = load_repo_metadata(test_file)
    assert result == test_data

def test_save_processed_data_creates_csv(tmp_path):
    """Test that save_processed_data creates a valid CSV file."""
    output_file = tmp_path / "output.csv"
    schema_file = tmp_path / "schema.yaml"
    
    # Create a dummy schema file (minimal valid YAML)
    schema_content = """
    type: object
    properties:
      pr_id: {type: string}
      repo_name: {type: string}
      turnaround_hours: {type: number}
    required: [pr_id, repo_name, turnaround_hours]
    """
    schema_file.write_text(schema_content)

    test_data = [
        {"pr_id": "1", "repo_name": "test", "turnaround_hours": 10.5},
        {"pr_id": "2", "repo_name": "test2", "turnaround_hours": 20.0}
    ]

    # Mock validate_json_schema to return True for this test
    with patch('save_processed_data.validate_json_schema', return_value=True):
        result = save_processed_data(test_data, output_file, schema_file)

    assert result is True
    assert output_file.exists()

    # Verify CSV content
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['pr_id'] == '1'
    assert rows[0]['turnaround_hours'] == '10.5'
