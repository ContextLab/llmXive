import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

from ingestion.add_disclaimer import process_json_file, process_csv_file, DISCLAIMER_TEXT

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_process_json_file_dict(temp_dir):
    file_path = temp_dir / "test.json"
    data = {"id": 1, "value": 0.5}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    process_json_file(file_path)
    
    with open(file_path, 'r') as f:
        result = json.load(f)
    
    assert '_disclaimer' in result
    assert result['_disclaimer'] == DISCLAIMER_TEXT
    assert result['id'] == 1

def test_process_json_file_list(temp_dir):
    file_path = temp_dir / "test_list.json"
    data = [{"id": 1, "value": 0.5}, {"id": 2, "value": 0.8}]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    process_json_file(file_path)
    
    with open(file_path, 'r') as f:
        result = json.load(f)
    
    assert isinstance(result, list)
    assert len(result) == 2
    for item in result:
        assert '_disclaimer' in item
        assert item['_disclaimer'] == DISCLAIMER_TEXT

def test_process_csv_file(temp_dir):
    file_path = temp_dir / "test.csv"
    data = [
        {"id": "1", "value": "0.5"},
        {"id": "2", "value": "0.8"}
    ]
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "value"])
        writer.writeheader()
        writer.writerows(data)
    
    process_csv_file(file_path)
    
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    for row in rows:
        assert '_disclaimer' in row
        assert row['_disclaimer'] == DISCLAIMER_TEXT
        assert row['id'] in ['1', '2']

def test_process_json_file_empty_list(temp_dir):
    file_path = temp_dir / "empty.json"
    with open(file_path, 'w') as f:
        json.dump([], f)
    
    # Should not raise, just log warning and return
    process_json_file(file_path)
    
    with open(file_path, 'r') as f:
        result = json.load(f)
    
    assert result == []

def test_process_nonexistent_file(temp_dir):
    file_path = temp_dir / "nonexistent.json"
    with pytest.raises(FileNotFoundError):
        process_csv_file(file_path)