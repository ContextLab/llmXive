import os
import yaml
import csv
from pathlib import Path
import pytest
from data_setup import ensure_directory, initialize_checksums_file, initialize_state_file

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Simulate the structure expected by data_setup.py
    # The script looks for parent of code/
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    return tmp_path

def test_ensure_directory_creates_new(tmp_path):
    new_dir = tmp_path / "new_folder"
    assert not new_dir.exists()
    ensure_directory(str(new_dir))
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_directory_exists(tmp_path):
    existing_dir = tmp_path / "existing_folder"
    existing_dir.mkdir()
    assert existing_dir.exists()
    ensure_directory(str(existing_dir)) # Should not raise
    assert existing_dir.exists()

def test_initialize_checksums_file_creates_new(tmp_path):
    checksums_file = tmp_path / "checksums.txt"
    initialize_checksums_file(str(checksums_file))
    
    assert checksums_file.exists()
    with open(checksums_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0] == ['filename', 'sha256_hash']

def test_initialize_checksums_file_preserves_existing(tmp_path):
    checksums_file = tmp_path / "checksums.txt"
    # Create with existing data
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksums_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'sha256_hash'])
        writer.writerow(['test.csv', 'abc123'])
    
    initialize_checksums_file(str(checksums_file))
    
    with open(checksums_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Should still have 2 rows (header + data)
    assert len(rows) == 2
    assert rows[1] == ['test.csv', 'abc123']

def test_initialize_state_file_creates_new(tmp_path):
    state_file = tmp_path / "state.yaml"
    initialize_state_file(str(state_file))
    
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "artifact_hashes" in data
    assert data["artifact_hashes"] == {}
    assert "updated_at" in data
    assert data["updated_at"] == "1970-01-01T00:00:00Z"

def test_initialize_state_file_preserves_existing(tmp_path):
    state_file = tmp_path / "state.yaml"
    # Create with existing data
    state_file.parent.mkdir(parents=True, exist_ok=True)
    existing_data = {
        "artifact_hashes": {"old_file.txt": "hash123"},
        "updated_at": "2023-01-01T00:00:00Z"
    }
    with open(state_file, 'w') as f:
        yaml.dump(existing_data, f)
    
    initialize_state_file(str(state_file))
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Should preserve existing data
    assert data["artifact_hashes"] == {"old_file.txt": "hash123"}
    assert data["updated_at"] == "2023-01-01T00:00:00Z"