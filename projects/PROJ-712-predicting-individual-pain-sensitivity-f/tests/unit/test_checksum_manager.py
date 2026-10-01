"""
Unit tests for the checksum manager module.
"""
import os
import tempfile
from pathlib import Path
import hashlib

import pytest
import yaml

# Import the module under test
# Note: In a real test environment, ensure the code/ directory is in sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_manager import (
    compute_sha256_file,
    scan_raw_data_directory,
    load_state_file,
    save_state_file,
    record_raw_data_checksums
)


def test_compute_sha256_file():
    """Test that SHA-256 checksum is computed correctly for a known file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        checksum = compute_sha256_file(temp_path)
        # Expected SHA-256 for "Hello, World!"
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        assert checksum == expected
    finally:
        temp_path.unlink()


def test_scan_raw_data_directory_empty():
    """Test scanning an empty directory returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = scan_raw_data_directory(Path(tmpdir))
        assert result == {}


def test_scan_raw_data_directory_with_files():
    """Test scanning a directory with files computes checksums correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create test files
        file1 = tmpdir_path / "file1.txt"
        file1.write_text("Test content 1")
        
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("Test content 2")

        result = scan_raw_data_directory(tmpdir_path)

        assert len(result) == 2
        
        # Check file1
        assert "file1.txt" in result
        expected1 = hashlib.sha256(b"Test content 1").hexdigest()
        assert result["file1.txt"] == expected1

        # Check file2 in subdirectory
        assert "subdir/file2.txt" in result
        expected2 = hashlib.sha256(b"Test content 2").hexdigest()
        assert result["subdir/file2.txt"] == expected2


def test_load_state_file_new():
    """Test loading a non-existent state file creates default structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "nonexistent.yaml"
        state = load_state_file(state_path)
        
        assert state["project_id"] == "PROJ-712-predicting-individual-pain-sensitivity-f"
        assert "state" in state
        assert "data_integrity" in state["state"]
        assert "checksums" in state["state"]["data_integrity"]


def test_load_state_file_existing():
    """Test loading an existing state file returns its contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        
        # Create a state file
        test_state = {
            "project_id": "TEST-001",
            "state": {
                "data_integrity": {
                    "checksums": {"file.txt": "abc123"}
                }
            }
        }
        with open(state_path, "w") as f:
            yaml.dump(test_state, f)

        loaded_state = load_state_file(state_path)
        assert loaded_state["project_id"] == "TEST-001"
        assert loaded_state["state"]["data_integrity"]["checksums"]["file.txt"] == "abc123"


def test_save_and_load_state_file():
    """Test saving and loading a state file preserves data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        
        test_state = {
            "project_id": "TEST-001",
            "state": {
                "data_integrity": {
                    "checksums": {"file.txt": "abc123", "file2.txt": "def456"}
                }
            }
        }
        
        save_state_file(state_path, test_state)
        loaded_state = load_state_file(state_path)
        
        assert loaded_state == test_state


def test_record_raw_data_checksums_integration():
    """Integration test for the full checksum recording workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create raw data directory structure
        raw_data_dir = tmpdir_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        
        # Create test files
        (raw_data_dir / "subject1.edf").write_text("EEG data 1")
        (raw_data_dir / "subject2.edf").write_text("EEG data 2")
        
        # Create state directory
        state_dir = tmpdir_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Run the function
        checksums = record_raw_data_checksums(tmpdir_path)
        
        # Verify checksums were computed
        assert len(checksums) == 2
        assert "data/raw/subject1.edf" in checksums
        assert "data/raw/subject2.edf" in checksums
        
        # Verify state file was updated
        state_file = state_dir / "PROJ-712-predicting-individual-pain-sensitivity-f.yaml"
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        assert state["state"]["data_integrity"]["checksums"]["data/raw/subject1.edf"] == checksums["data/raw/subject1.edf"]
        assert state["state"]["data_integrity"]["checksums"]["data/raw/subject2.edf"] == checksums["data/raw/subject2.edf"]
