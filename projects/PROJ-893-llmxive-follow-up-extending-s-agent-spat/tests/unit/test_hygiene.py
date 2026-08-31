"""
Unit tests for the hygiene module.
"""
import os
import tempfile
import yaml
import hashlib
from pathlib import Path
import pytest

# Import the functions we are testing
# We assume the test is run from the project root or code directory
# Adjusting import path for test execution context
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from hygiene import compute_sha256, scan_directory_for_hashes, load_state_yaml, save_state_yaml

def test_compute_sha256():
    """Test that compute_sha256 returns the correct hash for a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = Path(tmp.name)
    
    try:
        # Expected hash for "Hello, World!"
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_scan_directory_for_hashes():
    """Test scanning a directory for hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hashes = scan_directory_for_hashes(tmp_path, tmp_path)
        
        assert len(hashes) == 1
        assert "test.txt" in hashes
        assert hashes["test.txt"] == hashlib.sha256(b"test content").hexdigest()

def test_load_state_yaml_new():
    """Test loading a non-existent state file returns a default structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        state = load_state_yaml(state_file)
        
        assert state["project_id"] == "PROJ-893-llmxive-follow-up-extending-s-agent-spat"
        assert "data_hygiene" in state
        assert "raw" in state["data_hygiene"]
        assert "derived" in state["data_hygiene"]

def test_save_and_load_state_yaml():
    """Test saving and loading state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.yaml"
        initial_state = {
            "project_id": "TEST",
            "last_updated": "2023-01-01",
            "data_hygiene": {"raw": {"a.txt": "hash1"}, "derived": {}}
        }
        
        save_state_yaml(state_file, initial_state)
        
        assert state_file.exists()
        
        loaded_state = load_state_yaml(state_file)
        assert loaded_state == initial_state

def test_scan_non_existent_directory():
    """Test scanning a directory that doesn't exist returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "non_existent"
        hashes = scan_directory_for_hashes(non_existent, non_existent)
        assert hashes == {}