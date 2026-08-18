"""
Tests for the data directory initialization script.
"""
import pytest
import os
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from setup_data_directories import (
    get_project_root, 
    create_directories, 
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)

class TestDataDirectories:
    """Test suite for data directory setup functionality."""

    def test_create_directories_structure(self, tmp_path):
        """Test that the required subdirectories are created."""
        # Create a temporary directory to simulate project root
        project_root = tmp_path
        expected_subdirs = ['raw', 'processed', 'models', 'simulation']
        
        created_dirs = create_directories(project_root)
        
        # Verify all expected directories exist
        for subdir in expected_subdirs:
            dir_path = project_root / 'data' / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_create_directories_return_value(self, tmp_path):
        """Test that create_directories returns the correct list of paths."""
        project_root = tmp_path
        expected_subdirs = ['raw', 'processed', 'models', 'simulation']
        
        created_dirs = create_directories(project_root)
        
        assert len(created_dirs) == len(expected_subdirs), \
            f"Expected {len(expected_subdirs)} directories, got {len(created_dirs)}"
        
        for i, subdir in enumerate(expected_subdirs):
            assert created_dirs[i].name == subdir, \
                f"Expected directory name {subdir}, got {created_dirs[i].name}"

    def test_checksum_computation(self, tmp_path):
        """Test that checksum computation works correctly."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text("test content")
        
        checksum = compute_file_checksum(test_file)
        
        assert isinstance(checksum, str), "Checksum should be a string"
        assert len(checksum) == 64, "SHA-256 checksum should be 64 characters"
        assert all(c in '0123456789abcdef' for c in checksum), \
            "Checksum should contain only hexadecimal characters"

    def test_checksum_deterministic(self, tmp_path):
        """Test that checksum computation is deterministic."""
        test_file = tmp_path / 'test.txt'
        test_file.write_text("test content")
        
        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)
        
        assert checksum1 == checksum2, "Checksums should be identical for same content"

    def test_save_and_load_checksums(self, tmp_path):
        """Test saving and loading checksums to/from JSON."""
        checksums = {
            '/path/to/dir1': 'abc123',
            '/path/to/dir2': 'def456'
        }
        
        output_path = tmp_path / 'checksums.json'
        save_checksums(checksums, output_path)
        
        assert output_path.exists(), "Checksum file was not created"
        
        loaded_checksums = load_checksums(output_path)
        
        assert loaded_checksums == checksums, "Loaded checksums should match original"

    def test_record_checksums(self, tmp_path):
        """Test recording checksums for directories."""
        project_root = tmp_path
        created_dirs = create_directories(project_root)
        
        checksums = {}
        updated_checksums = record_checksums(created_dirs, checksums)
        
        assert len(updated_checksums) == len(created_dirs), \
            "Should have recorded checksums for all created directories"
        
        for dir_path in created_dirs:
            assert str(dir_path) in updated_checksums, \
                f"Checksum for {dir_path} not recorded"

    def test_verify_integrity_success(self, tmp_path):
        """Test integrity verification when directories exist."""
        project_root = tmp_path
        created_dirs = create_directories(project_root)
        
        checksums = {}
        checksums = record_checksums(created_dirs, checksums)
        
        assert verify_integrity(checksums), \
            "Integrity verification should pass for existing directories"

    def test_verify_integrity_failure_missing_dir(self, tmp_path):
        """Test integrity verification when a directory is missing."""
        project_root = tmp_path
        create_directories(project_root)
        
        # Remove one directory
        missing_dir = project_root / 'data' / 'raw'
        missing_dir.rmdir()
        
        # Create a checksum dict that expects the missing directory
        checksums = {
            str(missing_dir): hashlib.sha256(str(missing_dir).encode()).hexdigest()
        }
        
        assert not verify_integrity(checksums), \
            "Integrity verification should fail for missing directory"

    def test_idempotency(self, tmp_path):
        """Test that running create_directories multiple times is safe."""
        project_root = tmp_path
        
        # Run twice
        created_dirs_1 = create_directories(project_root)
        created_dirs_2 = create_directories(project_root)
        
        # Should return the same number of directories
        assert len(created_dirs_1) == len(created_dirs_2), \
            "Running create_directories multiple times should be idempotent"
        
        # All directories should still exist
        for dir_path in created_dirs_2:
            assert dir_path.exists(), f"Directory {dir_path} should still exist"