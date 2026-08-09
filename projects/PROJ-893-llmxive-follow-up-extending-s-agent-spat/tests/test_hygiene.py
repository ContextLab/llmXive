"""
Unit tests for the code/hygiene.py module.

Tests verify that SHA-256 hashing logic works correctly on known inputs
and that the state file update mechanism functions as expected.
"""
import os
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest

# Import the module under test
# We need to add the code directory to the path if not already there
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from hygiene import compute_sha256, scan_directory_for_hashes, load_state_yaml, save_state_yaml

def test_compute_sha256_string():
    """Test SHA-256 hash computation on a simple string content."""
    content = b"Hello, World!"
    expected_hash = hashlib.sha256(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        actual_hash = compute_sha256(tmp_path)
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        os.unlink(tmp_path)

def test_compute_sha256_empty_file():
    """Test SHA-256 hash computation on an empty file."""
    content = b""
    expected_hash = hashlib.sha256(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        actual_hash = compute_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_scan_directory_for_hashes():
    """Test scanning a directory for hashes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Create subdirectory
        subdir = base_path / "subdir"
        subdir.mkdir()
        
        # Create files
        file1 = base_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = subdir / "file2.txt"
        file2.write_text("content2")
        
        # Run scan
        hashes = scan_directory_for_hashes(base_path, base_path)
        
        # Verify keys exist
        assert "file1.txt" in hashes
        assert "subdir/file2.txt" in hashes or "subdir\\file2.txt" in hashes # Handle Windows path separator
        
        # Verify values are correct hashes
        expected_hash1 = hashlib.sha256(b"content1").hexdigest()
        expected_hash2 = hashlib.sha256(b"content2").hexdigest()
        
        # Normalize path key for assertion
        key2 = "subdir/file2.txt" if "subdir/file2.txt" in hashes else "subdir\\file2.txt"
        
        assert hashes["file1.txt"] == expected_hash1
        assert hashes[key2] == expected_hash2

def test_scan_directory_nonexistent():
    """Test scanning a non-existent directory returns empty dict."""
    fake_path = Path("/nonexistent/path/12345")
    hashes = scan_directory_for_hashes(fake_path, fake_path)
    assert hashes == {}

def test_load_save_state_yaml():
    """Test loading and saving state YAML."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_file = Path(tmp_dir) / "state.yaml"
        
        # Test save
        test_state = {
            "project_id": "TEST-001",
            "data_hygiene": {
                "raw": {"file.txt": "hash123"},
                "derived": {}
            }
        }
        save_state_yaml(state_file, test_state)
        
        assert state_file.exists()
        
        # Test load
        loaded_state = load_state_yaml(state_file)
        assert loaded_state["project_id"] == "TEST-001"
        assert loaded_state["data_hygiene"]["raw"]["file.txt"] == "hash123"

def test_load_state_yaml_nonexistent():
    """Test loading a non-existent state file returns default structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        state_file = Path(tmp_dir) / "nonexistent.yaml"
        
        state = load_state_yaml(state_file)
        
        assert "project_id" in state or state == {} # Depending on implementation, might return empty or default
        # Based on hygiene.py implementation, it returns {} if file doesn't exist
        assert state == {}