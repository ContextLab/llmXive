"""
Tests for directory setup and verification functionality.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import (
    compute_file_checksum,
    setup_directories,
    generate_checksums,
    verify_directories,
    REQUIRED_DIRS,
    PROJECT_ROOT,
)


class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""

    def test_compute_checksum_basic(self, tmp_path):
        """Test basic checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum1)

    def test_compute_checksum_empty_file(self, tmp_path):
        """Test checksum computation for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        
        checksum = compute_file_checksum(test_file)
        assert checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_compute_checksum_binary(self, tmp_path):
        """Test checksum computation for binary file."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\x04')
        
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64


class TestSetupDirectories:
    """Tests for setup_directories function."""

    def test_setup_directories_creates_all_dirs(self, tmp_path, monkeypatch):
        """Test that setup_directories creates all required directories."""
        # Mock PROJECT_ROOT to use tmp_path
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        created = setup_directories()
        
        # Check that all required directories were created
        for dir_path in REQUIRED_DIRS:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_setup_directories_idempotent(self, tmp_path, monkeypatch):
        """Test that setup_directories can be run multiple times."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        # Run twice
        created1 = setup_directories()
        created2 = setup_directories()
        
        # Second run should create nothing
        assert len(created2) == 0


class TestGenerateChecksums:
    """Tests for generate_checksums function."""

    def test_generate_checksums_basic(self, tmp_path, monkeypatch):
        """Test basic checksum generation."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        # Create test structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "test.txt"
        test_file.write_text("Test content")
        
        checksums = generate_checksums()
        
        assert "data/test.txt" in checksums
        assert len(checksums["data/test.txt"]) == 64

    def test_generate_checksums_manifest_created(self, tmp_path, monkeypatch):
        """Test that manifest file is created."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        generate_checksums()
        
        manifest_path = tmp_path / "data" / "checksums.manifest"
        assert manifest_path.exists()
        assert manifest_path.is_file()


class TestVerifyDirectories:
    """Tests for verify_directories function."""

    def test_verify_directories_success(self, tmp_path, monkeypatch):
        """Test successful verification."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        # Setup directories and generate checksums
        setup_directories()
        generate_checksums()
        
        success, errors = verify_directories()
        
        assert success
        assert len(errors) == 0

    def test_verify_directories_missing_file(self, tmp_path, monkeypatch):
        """Test verification with missing file."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        # Setup directories
        setup_directories()
        
        # Create a file but don't generate checksums
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "test.txt"
        test_file.write_text("Test")
        
        success, errors = verify_directories()
        
        assert not success
        assert any("Checksum manifest not found" in error for error in errors)

    def test_verify_directories_checksum_mismatch(self, tmp_path, monkeypatch):
        """Test verification with checksum mismatch."""
        monkeypatch.setattr("setup_directories.PROJECT_ROOT", tmp_path)
        
        # Setup directories and generate checksums
        setup_directories()
        generate_checksums()
        
        # Modify a file
        data_dir = tmp_path / "data"
        test_file = data_dir / "test.txt"
        test_file.write_text("Modified content")
        
        success, errors = verify_directories()
        
        assert not success
        assert any("Checksum mismatch" in error for error in errors)
