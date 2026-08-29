"""
Unit tests for T006: SHA-256 checksum tracking functionality.

Tests verify that:
1. SHA-256 hashes are computed correctly for known files
2. Directory scanning works as expected
3. State file updates are performed correctly
4. Empty directories are handled gracefully
"""
import os
import tempfile
import hashlib
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.ingest.track_checksums import (
    compute_sha256,
    scan_directory,
    load_state,
    save_state,
    update_checksums
)

class TestComputeSha256:
    """Tests for the compute_sha256 function."""
    
    def test_compute_sha256_known_string(self, tmp_path):
        """Test SHA-256 computation with a known string."""
        test_content = b"Hello, World!"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)
        
        result = compute_sha256(test_file)
        
        assert result == expected_hash
    
    def test_compute_sha256_large_file(self, tmp_path):
        """Test SHA-256 computation with a larger file (chunked reading)."""
        # Create a file larger than the chunk size (4096 bytes)
        chunk_size = 4096
        large_content = b"x" * (chunk_size * 3 + 100)
        expected_hash = hashlib.sha256(large_content).hexdigest()
        
        test_file = tmp_path / "large.bin"
        test_file.write_bytes(large_content)
        
        result = compute_sha256(test_file)
        
        assert result == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation with an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        result = compute_sha256(test_file)
        
        assert result == expected_hash

class TestScanDirectory:
    """Tests for the scan_directory function."""
    
    def test_scan_directory_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = scan_directory(tmp_path)
        
        assert len(result) == 1
        assert "test.txt" in result
        assert result["test.txt"] == hashlib.sha256(b"content").hexdigest()
    
    def test_scan_directory_nested(self, tmp_path):
        """Test scanning a directory with nested subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = subdir / "file2.txt"
        file2.write_text("content2")
        
        result = scan_directory(tmp_path)
        
        assert len(result) == 2
        assert "file1.txt" in result
        assert "subdir/file2.txt" in result
    
    def test_scan_directory_empty(self, tmp_path):
        """Test scanning an empty directory."""
        result = scan_directory(tmp_path)
        
        assert result == {}
    
    def test_scan_directory_nonexistent(self, tmp_path):
        """Test scanning a non-existent directory."""
        fake_path = tmp_path / "nonexistent"
        
        result = scan_directory(fake_path)
        
        assert result == {}

class TestLoadSaveState:
    """Tests for state file loading and saving."""
    
    def test_load_state_existing(self, tmp_path):
        """Test loading an existing state file."""
        state_file = tmp_path / "state.yaml"
        initial_state = {
            "project_id": "TEST-001",
            "artifact_hashes": {"data": {"file.txt": "abc123"}}
        }
        
        with open(state_file, "w") as f:
            yaml.safe_dump(initial_state, f)
        
        result = load_state(state_file)
        
        assert result["project_id"] == "TEST-001"
        assert result["artifact_hashes"]["data"]["file.txt"] == "abc123"
    
    def test_load_state_nonexistent(self, tmp_path):
        """Test loading a non-existent state file creates default structure."""
        state_file = tmp_path / "nonexistent.yaml"
        
        result = load_state(state_file)
        
        assert result["project_id"] is not None
        assert "artifact_hashes" in result
        assert result["last_updated"] is None
    
    def test_save_state(self, tmp_path):
        """Test saving state to a file."""
        state_file = tmp_path / "state.yaml"
        test_state = {
            "project_id": "TEST-002",
            "artifact_hashes": {"raw": {"data.txt": "def456"}},
            "last_updated": "2024-01-01T00:00:00"
        }
        
        save_state(test_state, state_file)
        
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["project_id"] == "TEST-002"
        assert loaded["artifact_hashes"]["raw"]["data.txt"] == "def456"

class TestUpdateChecksums:
    """Tests for the update_checksums function."""
    
    def test_update_checksums_creates_state(self, tmp_path):
        """Test that update_checksums creates state file if it doesn't exist."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        state_file = tmp_path / "state.yaml"
        
        test_file = data_dir / "test.txt"
        test_file.write_text("test content")
        
        result = update_checksums(data_dir, state_file)
        
        assert state_file.exists()
        assert "test.txt" in result
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        assert "artifact_hashes" in state
        assert "data/raw" in state["artifact_hashes"]
    
    def test_update_checksums_updates_existing(self, tmp_path):
        """Test that update_checksums updates existing state."""
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        state_file = tmp_path / "state.yaml"
        
        # Create initial state
        initial_state = {
            "project_id": "EXISTING",
            "artifact_hashes": {"other": {"old.txt": "oldhash"}},
            "last_updated": "2023-01-01T00:00:00"
        }
        with open(state_file, "w") as f:
            yaml.safe_dump(initial_state, f)
        
        # Add a file
        test_file = data_dir / "new.txt"
        test_file.write_text("new content")
        
        result = update_checksums(data_dir, state_file)
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        # Verify new data was added
        assert state["artifact_hashes"]["data/raw"]["new.txt"] == result["new.txt"]
        # Verify old data was preserved
        assert state["artifact_hashes"]["other"]["old.txt"] == "oldhash"
        # Verify timestamp was updated
        assert state["last_updated"] != "2023-01-01T00:00:00"