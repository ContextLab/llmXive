import os
import tempfile
import yaml
from pathlib import Path
import pytest
from utils.update_state import (
    compute_file_hash,
    scan_data_directory,
    load_or_create_state,
    update_state_file,
    update_state,
)

def test_compute_file_hash(tmp_path):
    """Test that compute_file_hash returns a valid SHA-256 hex string."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    
    hash_val = compute_file_hash(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)

def test_compute_file_hash_unchanged(tmp_path):
    """Test that hashing the same file twice yields the same result."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    
    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)
    assert hash1 == hash2

def test_scan_data_directory_empty(tmp_path):
    """Test scanning an empty directory returns empty dict."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    result = scan_data_directory(data_dir)
    assert result == {}

def test_scan_data_directory_with_files(tmp_path):
    """Test scanning a directory with files returns correct hashes."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    file1 = data_dir / "file1.txt"
    file1.write_text("Content 1")
    
    file2 = data_dir / "subdir" / "file2.txt"
    file2.parent.mkdir()
    file2.write_text("Content 2")
    
    result = scan_data_directory(data_dir)
    
    assert "file1.txt" in result
    assert "subdir/file2.txt" in result
    assert len(result) == 2

def test_load_or_create_state_new(tmp_path):
    """Test loading a non-existent state file creates a minimal skeleton."""
    state_file = tmp_path / "state.yaml"
    
    result = load_or_create_state(state_file)
    
    assert result["project"] == "PROJ-204-quantifying-the-impact-of-spatial-correl"
    assert result["artifact_hashes"] == {}
    assert result["last_updated"] is None
    assert state_file.exists()

def test_load_or_create_state_existing(tmp_path):
    """Test loading an existing state file returns its content."""
    state_file = tmp_path / "state.yaml"
    existing_data = {
        "project": "TEST-PROJECT",
        "artifact_hashes": {"old.txt": "abc123"},
        "last_updated": "2023-01-01"
    }
    state_file.write_text(yaml.dump(existing_data))
    
    result = load_or_create_state(state_file)
    
    assert result["project"] == "TEST-PROJECT"
    assert result["artifact_hashes"]["old.txt"] == "abc123"

def test_update_state_file(tmp_path):
    """Test updating state file with new hashes."""
    state_file = tmp_path / "state.yaml"
    new_hashes = {"file1.txt": "hash1", "file2.txt": "hash2"}
    
    update_state_file(state_file, new_hashes)
    
    assert state_file.exists()
    with state_file.open("r") as f:
        content = yaml.safe_load(f)
    
    assert content["artifact_hashes"]["file1.txt"] == "hash1"
    assert content["artifact_hashes"]["file2.txt"] == "hash2"
    assert "last_updated" in content
    assert content["project"] == "PROJ-204-quantifying-the-impact-of-spatial-correl"

def test_update_state_file_merges(tmp_path):
    """Test that update_state_file merges new hashes with existing ones."""
    state_file = tmp_path / "state.yaml"
    
    # First update
    update_state_file(state_file, {"file1.txt": "hash1"})
    
    # Second update
    update_state_file(state_file, {"file2.txt": "hash2"})
    
    with state_file.open("r") as f:
        content = yaml.safe_load(f)
    
    assert content["artifact_hashes"]["file1.txt"] == "hash1"
    assert content["artifact_hashes"]["file2.txt"] == "hash2"

def test_update_state_integration(tmp_path):
    """Test the full update_state workflow."""
    # Create a temporary data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    
    # Create some dummy files
    (data_dir / "raw" / "sample1.csv").write_text("col1,col2\n1,2")
    (data_dir / "processed" / "result.csv").write_text("metric,value\nacc,0.95")
    
    # Create a temporary state directory
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "PROJ-204-quantifying-the-impact-of-spatial-correl.yaml"
    
    # Run update_state with custom paths
    # We need to patch the internal paths or use the function with args
    # Since update_state uses hardcoded paths relative to CWD, we'll test scan and update directly
    artifact_hashes = scan_data_directory(data_dir)
    update_state_file(state_file, artifact_hashes)
    
    # Verify state file
    assert state_file.exists()
    with state_file.open("r") as f:
        content = yaml.safe_load(f)
    
    assert "raw/sample1.csv" in content["artifact_hashes"]
    assert "processed/result.csv" in content["artifact_hashes"]
    assert len(content["artifact_hashes"]) == 2
