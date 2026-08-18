"""
Tests for the data directory setup functionality.
"""
import os
import pytest
from pathlib import Path
import tempfile
import json
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_data_directories import (
    get_project_root,
    create_directories,
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)

class TestDataDirectorySetup:
    """Test suite for data directory creation and management."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create dummy code directory to simulate project root
            (tmp_path / 'code').mkdir()
            (tmp_path / 'data').mkdir()
            yield tmp_path

    def test_create_directories_structure(self, temp_project_root):
        """Test that all required data subdirectories are created."""
        created = create_directories(temp_project_root)
        
        expected_subdirs = ['raw', 'processed', 'models', 'simulation']
        
        for subdir in expected_subdirs:
            dir_path = temp_project_root / 'data' / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"
        
        assert len(created) == 4, f"Expected 4 directories, got {len(created)}"

    def test_create_directories_idempotent(self, temp_project_root):
        """Test that creating directories again does not fail."""
        # First creation
        create_directories(temp_project_root)
        # Second creation should not raise
        create_directories(temp_project_root)
        
        # Verify all still exist
        expected_subdirs = ['raw', 'processed', 'models', 'simulation']
        for subdir in expected_subdirs:
            assert (temp_project_root / 'data' / subdir).exists()

    def test_checksum_computation(self, temp_project_root):
        """Test checksum computation on a file."""
        test_file = temp_project_root / 'data' / 'test.txt'
        test_file.write_text("test content")
        
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64, "SHA-256 checksum should be 64 hex characters"
        assert all(c in '0123456789abcdef' for c in checksum), "Checksum should be hex"

    def test_checksum_save_load(self, temp_project_root):
        """Test saving and loading checksums."""
        checksums = {
            '/path/to/dir1': 'abc123',
            '/path/to/dir2': 'def456'
        }
        
        checksum_file = temp_project_root / 'data' / 'test_checksums.json'
        save_checksums(checksums, checksum_file)
        
        assert checksum_file.exists(), "Checksum file was not created"
        
        loaded = load_checksums(checksum_file)
        assert loaded == checksums, "Loaded checksums do not match saved"

    def test_verify_integrity(self, temp_project_root):
        """Test integrity verification."""
        # Create directories
        created = create_directories(temp_project_root)
        
        # Record checksums
        checksums = {}
        record_checksums(created, checksums)
        
        # Verify should pass
        assert verify_integrity(checksums), "Integrity verification should pass for existing directories"

    def test_verify_integrity_missing_dir(self, temp_project_root):
        """Test integrity verification with missing directory."""
        checksums = {
            str(temp_project_root / 'data' / 'raw'): 'somehash',
            str(temp_project_root / 'data' / 'nonexistent'): 'somehash'
        }
        
        assert not verify_integrity(checksums), "Integrity verification should fail for missing directory"

    def test_get_project_root_detection(self, temp_project_root):
        """Test project root detection logic."""
        # Change to code directory
        code_dir = temp_project_root / 'code'
        original_cwd = os.getcwd()
        try:
            os.chdir(code_dir)
            detected = get_project_root()
            assert detected == temp_project_root, f"Detected root {detected} != expected {temp_project_root}"
        finally:
            os.chdir(original_cwd)