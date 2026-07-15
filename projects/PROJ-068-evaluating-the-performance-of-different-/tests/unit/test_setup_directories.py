import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the functions to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_directories import (
    setup_directories,
    verify_directories,
    compute_file_checksum,
    generate_checksums,
    CHECKSUM_FILE
)


class TestSetupDirectories:
    """Tests for directory setup functionality."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_creates_required_dirs(self):
        """Test that setup_directories creates all required directories."""
        created = setup_directories(self.temp_dir)
        
        # Check that directories were created
        for dir_name in ["data/processed", "results/benchmarks", "results/figures", "results/analysis", "data/raw"]:
            full_path = os.path.join(self.temp_dir, dir_name)
            assert os.path.isdir(full_path), f"Directory {full_path} was not created"
        
        # Check return value
        assert len(created) > 0
        for path in created:
            assert os.path.isdir(path)

    def test_setup_idempotent(self):
        """Test that running setup again doesn't fail or duplicate."""
        first_run = setup_directories(self.temp_dir)
        second_run = setup_directories(self.temp_dir)
        
        # Should not raise errors
        assert len(second_run) == 0  # No new directories created


class TestVerifyDirectories:
    """Tests for directory verification functionality."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        # Setup the directories first
        setup_directories(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_verify_passes_when_dirs_exist(self):
        """Test that verify_directories returns success when all dirs exist."""
        success, details = verify_directories(self.temp_dir)
        
        assert success is True
        assert details["status"] == "success"
        assert len(details["missing_dirs"]) == 0
        assert details["checksum_status"] == "no_file"

    def test_verify_detects_missing_dirs(self):
        """Test that verify_directories detects missing directories."""
        # Remove one directory
        os.rmdir(os.path.join(self.temp_dir, "data/processed"))
        
        success, details = verify_directories(self.temp_dir)
        
        assert success is False
        assert "data/processed" in details["missing_dirs"]


class TestChecksums:
    """Tests for checksum functionality."""

    def setup_method(self):
        """Create a temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        setup_directories(self.temp_dir)
        
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, "data/processed", "test.txt")
        with open(test_file_path, "w") as f:
            f.write("test content for checksum verification")

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_file_checksum(self):
        """Test that compute_file_checksum returns a valid hash."""
        file_path = os.path.join(self.temp_dir, "data/processed", "test.txt")
        
        checksum = compute_file_checksum(file_path)
        
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_compute_file_checksum_file_not_found(self):
        """Test that compute_file_checksum raises error for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(os.path.join(self.temp_dir, "nonexistent.txt"))

    def test_generate_checksums(self):
        """Test that generate_checksums creates a valid checksum dict."""
        checksums = generate_checksums(self.temp_dir)
        
        assert "data/processed/test.txt" in checksums
        assert len(checksums["data/processed/test.txt"]) == 64

    def test_verify_with_checksum_file(self):
        """Test that verify_directories works with a checksum file."""
        # Generate and save checksums
        checksums = generate_checksums(self.temp_dir)
        checksum_file = os.path.join(self.temp_dir, CHECKSUM_FILE)
        with open(checksum_file, "w") as f:
            json.dump(checksums, f)
        
        # Verify should pass
        success, details = verify_directories(self.temp_dir)
        
        assert success is True
        assert details["checksum_status"] == "verified"

    def test_verify_detects_checksum_mismatch(self):
        """Test that verify_directories detects checksum mismatches."""
        # Generate and save checksums
        checksums = generate_checksums(self.temp_dir)
        checksum_file = os.path.join(self.temp_dir, CHECKSUM_FILE)
        with open(checksum_file, "w") as f:
            json.dump(checksums, f)
        
        # Modify the file
        test_file_path = os.path.join(self.temp_dir, "data/processed", "test.txt")
        with open(test_file_path, "w") as f:
            f.write("modified content")
        
        # Verify should fail
        success, details = verify_directories(self.temp_dir)
        
        assert success is False
        assert details["checksum_status"] == "failed"
        assert details["checksum_details"]["data/processed/test.txt"] == "mismatch"