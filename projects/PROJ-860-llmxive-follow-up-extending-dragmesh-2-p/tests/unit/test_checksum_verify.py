"""
Unit tests for checksum verification functionality.
"""
import os
import sys
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_verify import (
    compute_sha256,
    scan_directory,
    load_existing_checksums,
    save_checksums,
    verify_data_integrity,
    update_checksums
)

class TestComputeSha256:
    def test_compute_sha256_known_file(self, tmp_path):
        """Test SHA256 computation on a file with known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        computed_hash = compute_sha256(test_file)
        
        assert computed_hash == expected_hash
    
    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        expected_hash = hashlib.sha256(b"").hexdigest()
        computed_hash = compute_sha256(test_file)
        
        assert computed_hash == expected_hash
    
    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

class TestScanDirectory:
    def test_scan_directory_single_level(self, tmp_path):
        """Test scanning a directory with files at single level."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        files = scan_directory(tmp_path)
        
        assert len(files) == 2
        assert all(f.is_file() for f in files)
    
    def test_scan_directory_nested(self, tmp_path):
        """Test scanning a directory with nested subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (subdir / "file2.txt").write_text("content2")
        
        files = scan_directory(tmp_path)
        
        assert len(files) == 2
    
    def test_scan_directory_empty(self, tmp_path):
        """Test scanning an empty directory."""
        files = scan_directory(tmp_path)
        assert len(files) == 0
    
    def test_scan_directory_nonexistent(self, tmp_path):
        """Test scanning a non-existent directory."""
        non_existent = tmp_path / "does_not_exist"
        files = scan_directory(non_existent)
        assert len(files) == 0

class TestLoadSaveChecksums:
    def test_load_nonexistent_state(self, tmp_path):
        """Test loading from a non-existent state file."""
        state_file = tmp_path / "state.yaml"
        state_data = load_existing_checksums(state_file)
        
        assert "artifact_hashes" in state_data
        assert "updated_at" in state_data
        assert state_data["artifact_hashes"] == {}
    
    def test_load_empty_state(self, tmp_path):
        """Test loading from an empty state file."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("{}")
        
        state_data = load_existing_checksums(state_file)
        
        assert state_data["artifact_hashes"] == {}
    
    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums."""
        state_file = tmp_path / "state.yaml"
        test_data = {
            "artifact_hashes": {"file1.txt": "abc123"},
            "updated_at": "2023-01-01T00:00:00"
        }
        
        save_checksums(state_file, test_data)
        loaded_data = load_existing_checksums(state_file)
        
        assert loaded_data == test_data

class TestUpdateChecksums:
    def test_update_checksums(self, tmp_path):
        """Test updating checksums for a directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        
        state_file = tmp_path / "state.yaml"
        state_data = update_checksums(state_file, [data_dir])
        
        assert len(state_data["artifact_hashes"]) == 2
        assert "data/file1.txt" in state_data["artifact_hashes"]
        assert "data/file2.txt" in state_data["artifact_hashes"]
        
        # Verify hashes are correct
        content1 = b"content1"
        expected_hash1 = hashlib.sha256(content1).hexdigest()
        assert state_data["artifact_hashes"]["data/file1.txt"] == expected_hash1
    
    def test_update_checksums_nonexistent_dir(self, tmp_path):
        """Test updating checksums with a non-existent directory."""
        non_existent = tmp_path / "does_not_exist"
        state_file = tmp_path / "state.yaml"
        
        state_data = update_checksums(state_file, [non_existent])
        
        assert state_data["artifact_hashes"] == {}

class TestVerifyDataIntegrity:
    def test_verify_all_match(self, tmp_path):
        """Test verification when all files match stored hashes."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file1.txt"
        test_file.write_text("content1")
        
        state_file = tmp_path / "state.yaml"
        content = b"content1"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        state_data = {
            "artifact_hashes": {"data/file1.txt": expected_hash},
            "updated_at": None
        }
        save_checksums(state_file, state_data)
        
        is_valid = verify_data_integrity(state_file, [data_dir])
        assert is_valid is True
    
    def test_verify_mismatch(self, tmp_path):
        """Test verification when a file hash doesn't match."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file1.txt"
        test_file.write_text("new content")
        
        state_file = tmp_path / "state.yaml"
        old_hash = hashlib.sha256(b"old content").hexdigest()
        
        state_data = {
            "artifact_hashes": {"data/file1.txt": old_hash},
            "updated_at": None
        }
        save_checksums(state_file, state_data)
        
        is_valid = verify_data_integrity(state_file, [data_dir])
        assert is_valid is False
    
    def test_verify_missing_file(self, tmp_path):
        """Test verification when a stored file is missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Create a different file
        (data_dir / "other.txt").write_text("other")
        
        state_file = tmp_path / "state.yaml"
        state_data = {
            "artifact_hashes": {"data/file1.txt": "abc123"},
            "updated_at": None
        }
        save_checksums(state_file, state_data)
        
        is_valid = verify_data_integrity(state_file, [data_dir])
        assert is_valid is False