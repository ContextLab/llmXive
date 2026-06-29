"""
Unit tests for checksum utilities.

These tests verify the SHA-256 checksum computation and tracking
functionality as required by Constitution III.
"""
import hashlib
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from src.utils.checksums import (
    compute_sha256,
    scan_directory_for_checksums,
    load_artifact_hashes,
    save_artifact_hashes,
    update_checksums_for_raw_data,
)


class TestComputeSha256:
    """Tests for SHA-256 computation function."""
    
    def test_compute_sha256_known_file(self, tmp_path):
        """Test SHA-256 computation on a file with known content."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Compute hash
        computed_hash = compute_sha256(test_file)
        
        # Verify against known SHA-256
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert computed_hash == expected_hash
        assert len(computed_hash) == 64  # SHA-256 produces 64 hex characters
    
    def test_compute_sha256_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        
        computed_hash = compute_sha256(empty_file)
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert computed_hash == expected_hash


class TestScanDirectoryForChecksums:
    """Tests for directory scanning function."""
    
    def test_scan_single_file(self, tmp_path):
        """Test scanning a directory with a single file."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2\n1,2\n")
        
        checksums = scan_directory_for_checksums(tmp_path)
        
        assert "test.csv" in checksums
        assert len(checksums) == 1
        assert len(checksums["test.csv"]) == 64
    
    def test_scan_multiple_files(self, tmp_path):
        """Test scanning a directory with multiple files."""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.json"
        file1.write_text("data1")
        file2.write_text("data2")
        
        checksums = scan_directory_for_checksums(tmp_path)
        
        assert "file1.csv" in checksums
        assert "file2.json" in checksums
        assert len(checksums) == 2
    
    def test_scan_recursive(self, tmp_path):
        """Test recursive directory scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = tmp_path / "file1.csv"
        file2 = subdir / "file2.csv"
        file1.write_text("data1")
        file2.write_text("data2")
        
        checksums = scan_directory_for_checksums(tmp_path)
        
        assert "file1.csv" in checksums
        assert "subdir/file2.csv" in checksums
        assert len(checksums) == 2
    
    def test_scan_with_extension_filter(self, tmp_path):
        """Test scanning with extension filter."""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.json"
        file1.write_text("data1")
        file2.write_text("data2")
        
        checksums = scan_directory_for_checksums(tmp_path, extensions=[".csv"])
        
        assert "file1.csv" in checksums
        assert "file2.json" not in checksums
        assert len(checksums) == 1
    
    def test_scan_nonexistent_directory(self, tmp_path):
        """Test that FileNotFoundError is raised for missing directory."""
        with pytest.raises(FileNotFoundError):
            scan_directory_for_checksums(tmp_path / "nonexistent")
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory returns empty dict."""
        checksums = scan_directory_for_checksums(tmp_path)
        assert checksums == {}


class TestLoadAndSaveArtifactHashes:
    """Tests for state file loading and saving."""
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent state file returns default structure."""
        state_file = tmp_path / "state.yaml"
        state_data = load_artifact_hashes(state_file)
        
        assert "project_id" in state_data
        assert "artifact_hashes" in state_data
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading state data."""
        state_file = tmp_path / "state.yaml"
        test_data = {
            "project_id": "TEST-001",
            "artifact_hashes": {
                "raw_data": {"file.csv": "abc123"}
            }
        }
        
        save_artifact_hashes(state_file, test_data)
        loaded_data = load_artifact_hashes(state_file)
        
        assert loaded_data == test_data
    
    def test_save_creates_parent_directory(self, tmp_path):
        """Test that save creates parent directories if needed."""
        state_file = tmp_path / "deep" / "nested" / "state.yaml"
        test_data = {"project_id": "TEST-001"}
        
        save_artifact_hashes(state_file, test_data)
        
        assert state_file.exists()


class TestUpdateChecksumsForRawData:
    """Tests for the main checksum tracking function."""
    
    def test_update_with_files(self, tmp_path):
        """Test updating checksums when files exist."""
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        state_file = tmp_path / "state.yaml"
        
        # Create test files
        (raw_data_dir / "test1.csv").write_text("data1")
        (raw_data_dir / "test2.csv").write_text("data2")
        
        state_data = update_checksums_for_raw_data(raw_data_dir, state_file)
        
        assert "project_id" in state_data
        assert "artifact_hashes" in state_data
        assert "raw_data" in state_data["artifact_hashes"]
        assert "test1.csv" in state_data["artifact_hashes"]["raw_data"]
        assert "test2.csv" in state_data["artifact_hashes"]["raw_data"]
    
    def test_update_preserves_existing_hashes(self, tmp_path):
        """Test that existing hashes are preserved when updating."""
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        state_file = tmp_path / "state.yaml"
        
        # Create initial state with existing hashes
        initial_data = {
            "project_id": "TEST-001",
            "artifact_hashes": {
                "existing_category": {"old_file.txt": "oldhash123"}
            }
        }
        save_artifact_hashes(state_file, initial_data)
        
        # Create a new raw file
        (raw_data_dir / "new.csv").write_text("new data")
        
        state_data = update_checksums_for_raw_data(raw_data_dir, state_file)
        
        # Verify existing hashes are preserved
        assert "existing_category" in state_data["artifact_hashes"]
        assert "old_file.txt" in state_data["artifact_hashes"]["existing_category"]
    
    def test_update_empty_directory(self, tmp_path):
        """Test updating checksums with empty raw data directory."""
        raw_data_dir = tmp_path / "data" / "raw"
        raw_data_dir.mkdir(parents=True)
        state_file = tmp_path / "state.yaml"
        
        state_data = update_checksums_for_raw_data(raw_data_dir, state_file)
        
        assert state_data["artifact_hashes"]["raw_data"] == {}
