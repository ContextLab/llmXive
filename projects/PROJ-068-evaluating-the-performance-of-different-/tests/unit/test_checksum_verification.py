"""
Unit tests for checksum verification functionality.

Tests the pre-commit checksum hook logic to ensure:
- Checksums are computed correctly
- Verification detects modifications
- Missing files are caught
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions we're testing
from tools.setup_directories import (
    compute_file_checksum,
    generate_checksums,
    verify_checksums,
    setup_directories,
)


class TestChecksumVerification:
    """Tests for checksum verification functionality."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create required directories
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "results" / "benchmarks").mkdir(parents=True)
        
        # Create some test files
        data_file = project_root / "data" / "processed" / "test_data.csv"
        data_file.write_text("col1,col2\n1,2\n3,4\n")
        
        result_file = project_root / "results" / "benchmarks" / "test_results.csv"
        result_file.write_text("size,latency\n100,1.5\n200,2.1\n")
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_compute_file_checksum(self, temp_project_dir):
        """Test that checksums are computed correctly and consistently."""
        file_path = temp_project_dir / "data" / "processed" / "test_data.csv"
        
        checksum1 = compute_file_checksum(file_path)
        checksum2 = compute_file_checksum(file_path)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex string
        assert all(c in '0123456789abcdef' for c in checksum1)

    def test_compute_file_checksum_nonexistent(self, temp_project_dir):
        """Test that non-existent files return empty string."""
        fake_path = temp_project_dir / "nonexistent" / "file.txt"
        checksum = compute_file_checksum(fake_path)
        assert checksum == ""

    def test_generate_checksums(self, temp_project_dir):
        """Test that checksums are generated for all files."""
        checksum_file = temp_project_dir / ".checksums.json"
        
        # Generate checksums
        success = generate_checksums()
        assert success
        assert checksum_file.exists()
        
        # Verify checksums were recorded
        with open(checksum_file, "r") as f:
            checksums = json.load(f)
        
        assert len(checksums) == 2
        assert any("test_data.csv" in key for key in checksums.keys())
        assert any("test_results.csv" in key for key in checksums.keys())

    def test_verify_checksums_valid(self, temp_project_dir):
        """Test verification passes for unchanged files."""
        # Generate checksums first
        generate_checksums()
        
        # Verify should pass
        success, errors = verify_checksums()
        assert success
        assert len(errors) == 0

    def test_verify_checksums_modified(self, temp_project_dir):
        """Test verification fails for modified files."""
        # Generate checksums first
        generate_checksums()
        
        # Modify a file
        data_file = temp_project_dir / "data" / "processed" / "test_data.csv"
        data_file.write_text("modified content\n")
        
        # Verify should fail
        success, errors = verify_checksums()
        assert not success
        assert len(errors) > 0
        assert any("Checksum mismatch" in error for error in errors)

    def test_verify_checksums_deleted(self, temp_project_dir):
        """Test verification fails for deleted files."""
        # Generate checksums first
        generate_checksums()
        
        # Delete a file
        data_file = temp_project_dir / "data" / "processed" / "test_data.csv"
        data_file.unlink()
        
        # Verify should fail
        success, errors = verify_checksums()
        assert not success
        assert len(errors) > 0
        assert any("missing but checksum exists" in error.lower() for error in errors)

    def test_setup_directories(self, temp_project_dir):
        """Test that setup creates required directories."""
        # Remove a directory
        results_dir = temp_project_dir / "results"
        shutil.rmtree(results_dir)
        
        # Setup should recreate it
        success = setup_directories()
        assert success
        assert results_dir.exists()
        assert (results_dir / "benchmarks").exists()

    def test_verify_checksums_empty_dir(self, temp_project_dir):
        """Test verification with no files in monitored directories."""
        # Remove all files
        for dir_path in [temp_project_dir / "data" / "processed", 
                       temp_project_dir / "results" / "benchmarks"]:
            for file_path in dir_path.iterdir():
                file_path.unlink()
        
        # Generate checksums (should create empty file)
        generate_checksums()
        
        # Verify should pass (no files to check)
        success, errors = verify_checksums()
        assert success
        assert len(errors) == 0