import json
import os
import tempfile
from pathlib import Path
import pytest

from save_data import load_json_file, save_json_file, save_csv_file, validate_and_save_processed_data

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_json_file(temp_dir):
    test_data = [{"key": "value", "number": 123}]
    file_path = temp_dir / "test.json"
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_json_file(str(file_path))
    assert loaded == test_data

def test_save_json_file(temp_dir):
    test_data = [{"key": "value", "number": 123}]
    file_path = temp_dir / "output.json"
    
    save_json_file(str(file_path), test_data)
    assert file_path.exists()
    
    with open(file_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == test_data

def test_save_csv_file(temp_dir):
    test_data = [
        {"id": 1, "name": "Alice", "score": 95.5},
        {"id": 2, "name": "Bob", "score": 87.3}
    ]
    file_path = temp_dir / "output.csv"
    
    save_csv_file(str(file_path), test_data)
    assert file_path.exists()
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3  # header + 2 data rows
    assert "id,name,score" in lines[0]

def test_save_csv_empty(temp_dir):
    file_path = temp_dir / "empty.csv"
    # Should not raise, just log warning
    save_csv_file(str(file_path), [])

def test_validate_and_save_processed_data(temp_dir):
    # Create a minimal valid schema file
    schema_content = """
    type: object
    properties:
      pr_id: {type: string}
      turnaround_hours: {type: number}
    required: [pr_id, turnaround_hours]
    """
    schema_file = temp_dir / "test_schema.yaml"
    with open(schema_file, 'w') as f:
        f.write(schema_content)
    
    valid_data = [{"pr_id": "123", "turnaround_hours": 24.5}]
    
    # This should return True for valid data
    result = validate_and_save_processed_data(valid_data, str(schema_file))
    assert result is True

def test_validate_invalid_data(temp_dir):
    # Create a schema requiring 'pr_id'
    schema_content = """
    type: object
    properties:
      pr_id: {type: string}
    required: [pr_id]
    """
    schema_file = temp_dir / "test_schema.yaml"
    with open(schema_file, 'w') as f:
        f.write(schema_content)
    
    # Data missing required field
    invalid_data = [{"turnaround_hours": 24.5}]
    
    # This should return False
    result = validate_and_save_processed_data(invalid_data, str(schema_file))
    assert result is False
