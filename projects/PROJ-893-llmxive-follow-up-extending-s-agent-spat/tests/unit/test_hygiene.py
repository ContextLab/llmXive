"""
Unit tests for the data hygiene module.
"""
import os
import sys
import json
import yaml
import tempfile
from pathlib import Path
import pytest

# Add code to path to allow imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from hygiene import compute_sha256, load_state_yaml, save_state_yaml, STATE_DIR, STATE_FILE_NAME

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        # Known hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        os.unlink(temp_path)

def test_load_state_yaml_new():
    """Test loading a non-existent state file returns default structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test_state.yaml"
        state = load_state_yaml(state_file)
        
        assert state["project_id"] == "PROJ-893-llmxive-follow-up-extending-s-agent-spat"
        assert "data_hygiene" in state
        assert "raw" in state["data_hygiene"]
        assert "derived" in state["data_hygiene"]

def test_save_and_load_state_yaml():
    """Test saving and loading state YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test_state.yaml"
        
        test_state = {
            "project_id": "TEST-001",
            "last_updated": "2023-01-01T00:00:00",
            "data_hygiene": {
                "raw": {"file1.txt": "abc123"},
                "derived": {}
            }
        }
        
        save_state_yaml(state_file, test_state)
        
        assert state_file.exists()
        
        loaded_state = load_state_yaml(state_file)
        
        assert loaded_state["project_id"] == "TEST-001"
        assert loaded_state["data_hygiene"]["raw"]["file1.txt"] == "abc123"

def test_scan_directory_integration():
    """Integration test for scanning a directory (mocked via hygiene imports)."""
    # Import the function here to avoid circular issues if needed, 
    # but since it's in hygiene, we can import directly if we fix path
    from hygiene import scan_directory_for_hashes
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_subdir"
        test_dir.mkdir()
        
        # Create a test file
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")
        
        hashes = scan_directory_for_hashes(test_dir, test_dir)
        
        assert len(hashes) == 1
        assert "test.txt" in hashes
        assert hashes["test.txt"] == compute_sha256(test_file)
