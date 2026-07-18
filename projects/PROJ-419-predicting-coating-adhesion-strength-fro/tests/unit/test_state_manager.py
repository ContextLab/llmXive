import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Import the module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from state_manager import (
    calculate_file_checksum,
    scan_raw_data_directory,
    generate_state_checksums,
    write_state_file,
    verify_state_checksums
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_data_file(temp_dir):
    """Create a sample data file for testing."""
    file_path = os.path.join(temp_dir, "test_data.csv")
    with open(file_path, 'w') as f:
        f.write("id,value\n1,10\n2,20\n3,30\n")
    return file_path

@pytest.fixture
def sample_raw_data_dir(temp_dir):
    """Create a sample raw data directory structure."""
    raw_dir = os.path.join(temp_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    # Create sample files
    file1 = os.path.join(raw_dir, "materials.csv")
    with open(file1, 'w') as f:
        f.write("material_id,composition\nMP001,Fe2O3\n")
    
    file2 = os.path.join(raw_dir, "surface_data.json")
    with open(file2, 'w') as f:
        f.write('{"sample_id": "NIST001", "roughness": 0.5}')
    
    # Create a nested directory
    nested_dir = os.path.join(raw_dir, "literature")
    os.makedirs(nested_dir, exist_ok=True)
    file3 = os.path.join(nested_dir, "papers.csv")
    with open(file3, 'w') as f:
        f.write("paper_id,year,citation\nP001,2020,150\n")
    
    return raw_dir

def test_calculate_file_checksum(sample_data_file):
    """Test checksum calculation for a single file."""
    checksum = calculate_file_checksum(sample_data_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_calculate_file_checksum_missing_file(temp_dir):
    """Test checksum calculation for a missing file raises error."""
    missing_file = os.path.join(temp_dir, "nonexistent.csv")
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(missing_file)

def test_scan_raw_data_directory(sample_raw_data_dir):
    """Test scanning directory for data files."""
    files = scan_raw_data_directory(sample_raw_data_dir)
    assert len(files) == 3
    
    filenames = [os.path.basename(f) for f in files]
    assert "materials.csv" in filenames
    assert "surface_data.json" in filenames
    assert "papers.csv" in filenames

def test_scan_raw_data_directory_empty(temp_dir):
    """Test scanning empty directory returns empty list."""
    empty_dir = os.path.join(temp_dir, "empty_data")
    os.makedirs(empty_dir, exist_ok=True)
    
    files = scan_raw_data_directory(empty_dir)
    assert files == []

def test_generate_state_checksums(sample_raw_data_dir, temp_dir):
    """Test generating checksums for all files in directory."""
    state_dir = os.path.join(temp_dir, "state")
    checksums = generate_state_checksums(sample_raw_data_dir, state_dir)
    
    assert len(checksums) == 3
    assert any("materials.csv" in k for k in checksums.keys())
    assert any("surface_data.json" in k for k in checksums.keys())
    assert any("papers.csv" in k for k in checksums.keys())

def test_write_state_file(temp_dir):
    """Test writing state file to disk."""
    state_dir = os.path.join(temp_dir, "state")
    checksums = {
        "test.csv": "abc123def456",
        "data.json": "789xyz000"
    }
    
    state_file = write_state_file(checksums, state_dir)
    
    assert os.path.exists(state_file)
    assert state_file.endswith("state_checksums.yaml")
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "files" in data
    assert "generated_at" in data
    assert "algorithm" in data
    assert data["files"] == checksums

def test_verify_state_checksums_success(sample_raw_data_dir, temp_dir):
    """Test successful checksum verification."""
    state_dir = os.path.join(temp_dir, "state")
    checksums = generate_state_checksums(sample_raw_data_dir, state_dir)
    state_file = write_state_file(checksums, state_dir)
    
    assert verify_state_checksums(state_file, sample_raw_data_dir) is True

def test_verify_state_checksums_missing_file(sample_raw_data_dir, temp_dir):
    """Test verification fails when file is missing."""
    state_dir = os.path.join(temp_dir, "state")
    checksums = generate_state_checksums(sample_raw_data_dir, state_dir)
    
    # Remove a file
    for rel_path in checksums.keys():
        if "materials.csv" in rel_path:
            full_path = os.path.join(sample_raw_data_dir, rel_path)
            os.remove(full_path)
            break
    
    state_file = write_state_file(checksums, state_dir)
    assert verify_state_checksums(state_file, sample_raw_data_dir) is False

def test_verify_state_checksums_corrupted_file(sample_raw_data_dir, temp_dir):
    """Test verification fails when file content is corrupted."""
    state_dir = os.path.join(temp_dir, "state")
    checksums = generate_state_checksums(sample_raw_data_dir, state_dir)
    state_file = write_state_file(checksums, state_dir)
    
    # Corrupt a file
    for rel_path in checksums.keys():
        if "materials.csv" in rel_path:
            full_path = os.path.join(sample_raw_data_dir, rel_path)
            with open(full_path, 'w') as f:
                f.write("corrupted data")
            break
    
    assert verify_state_checksums(state_file, sample_raw_data_dir) is False
