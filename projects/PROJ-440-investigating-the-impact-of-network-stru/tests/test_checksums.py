import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the module under test
from code.utils.checksums import (
    compute_file_checksum,
    generate_checksum_file,
    verify_checksums,
    verify_single_file,
    setup_data_directories,
    register_artifacts
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking the project data layout."""
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir)
    os.makedirs(os.path.join(data_dir, "raw"))
    os.makedirs(os.path.join(data_dir, "processed"))
    os.makedirs(os.path.join(data_dir, "analysis"))
    
    # Create some dummy files
    with open(os.path.join(data_dir, "raw", "test1.csv"), "w") as f:
        f.write("id,value\n1,10\n2,20\n")
    with open(os.path.join(data_dir, "processed", "test2.csv"), "w") as f:
        f.write("graph_id,decay_rate\n1,0.5\n")
    
    yield data_dir
    
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    temp_dir = tempfile.mkdtemp()
    state_dir = os.path.join(temp_dir, "state", "projects")
    os.makedirs(state_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_compute_file_checksum(temp_data_dir):
    """Test that compute_file_checksum returns a valid SHA256 hex string."""
    file_path = os.path.join(temp_data_dir, "raw", "test1.csv")
    checksum = compute_file_checksum(file_path)
    
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_generate_checksum_file(temp_data_dir, tmp_path):
    """Test that generate_checksum_file creates a valid JSON checksum file."""
    output_path = str(tmp_path / "checksums.json")
    generate_checksum_file(temp_data_dir, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        checksums = json.load(f)
    
    # Check that our test files are present (excluding .gitkeep if any)
    assert any("test1.csv" in k for k in checksums.keys())
    assert any("test2.csv" in k for k in checksums.keys())
    # Check that .gitkeep files are excluded
    assert not any(".gitkeep" in k for k in checksums.keys())

def test_verify_checksums_success(temp_data_dir, tmp_path):
    """Test successful verification when files are unchanged."""
    checksum_file = str(tmp_path / "checksums.json")
    generate_checksum_file(temp_data_dir, checksum_file)
    
    is_valid = verify_checksums(checksum_file, temp_data_dir)
    assert is_valid is True

def test_verify_checksums_failure_modified(temp_data_dir, tmp_path):
    """Test verification fails when a file is modified."""
    checksum_file = str(tmp_path / "checksums.json")
    generate_checksum_file(temp_data_dir, checksum_file)
    
    # Modify a file
    file_path = os.path.join(temp_data_dir, "raw", "test1.csv")
    with open(file_path, "w") as f:
        f.write("modified content")
    
    is_valid = verify_checksums(checksum_file, temp_data_dir)
    assert is_valid is False

def test_verify_checksums_failure_missing(temp_data_dir, tmp_path):
    """Test verification fails when a file is missing."""
    checksum_file = str(tmp_path / "checksums.json")
    generate_checksum_file(temp_data_dir, checksum_file)
    
    # Delete a file
    file_path = os.path.join(temp_data_dir, "raw", "test1.csv")
    os.remove(file_path)
    
    is_valid = verify_checksums(checksum_file, temp_data_dir)
    assert is_valid is False

def test_verify_single_file(temp_data_dir):
    """Test verify_single_file against a known checksum."""
    file_path = os.path.join(temp_data_dir, "raw", "test1.csv")
    checksum = compute_file_checksum(file_path)
    
    assert verify_single_file(file_path, checksum) is True
    assert verify_single_file(file_path, "invalid_checksum") is False

def test_setup_data_directories(tmp_path):
    """Test that setup_data_directories creates the required subdirectories."""
    base_path = str(tmp_path / "new_data")
    setup_data_directories(base_path)
    
    assert os.path.isdir(base_path)
    assert os.path.isdir(os.path.join(base_path, "raw"))
    assert os.path.isdir(os.path.join(base_path, "processed"))
    assert os.path.isdir(os.path.join(base_path, "analysis"))

def test_register_artifacts(temp_data_dir, temp_state_dir):
    """Test that register_artifacts updates the state file correctly."""
    checksum_file = os.path.join(temp_data_dir, ".checksums.json")
    generate_checksum_file(temp_data_dir, checksum_file)
    
    state_file = os.path.join(temp_state_dir, "state", "projects", "test_proj.yaml")
    register_artifacts(state_file, checksum_file, temp_data_dir)
    
    assert os.path.exists(state_file)
    
    import yaml
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert 'last_checksum_run' in state
    assert 'data_checksums' in state
    assert len(state['data_checksums']) > 0
    assert 'test1.csv' in str(state['data_checksums'])
