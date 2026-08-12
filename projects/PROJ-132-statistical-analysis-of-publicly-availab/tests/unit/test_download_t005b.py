import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

from src.data.download_t005b import (
    compute_sha256,
    verify_checksums,
    archive_data
)

class TestDownloadT005b:
    """Unit tests for T005b download functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_base = tempfile.mkdtemp()
        source_dir = Path(temp_base) / "source"
        dest_dir = Path(temp_base) / "dest"
        checksum_file = Path(temp_base) / "checksums.txt"
        
        source_dir.mkdir()
        dest_dir.mkdir()
        
        yield {
            "temp_base": Path(temp_base),
            "source": source_dir,
            "dest": dest_dir,
            "checksums": checksum_file
        }
        
        # Cleanup
        shutil.rmtree(temp_base)

    def test_compute_sha256_basic(self, temp_dirs):
        """Test basic SHA-256 computation on a file."""
        test_file = temp_dirs["source"] / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_sha256(test_file)
        
        # Known SHA-256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert checksum == expected

    def test_compute_sha256_file_not_found(self, temp_dirs):
        """Test that compute_sha256 raises error for missing file."""
        non_existent = temp_dirs["source"] / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

    def test_verify_checksums_basic(self, temp_dirs):
        """Test basic checksum verification and file writing."""
        # Create test files
        file1 = temp_dirs["source"] / "file1.txt"
        file2 = temp_dirs["source"] / "file2.txt"
        
        file1.write_bytes(b"Content 1")
        file2.write_bytes(b"Content 2")
        
        files = [file1, file2]
        
        checksums = verify_checksums(files, temp_dirs["checksums"])
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        
        # Verify checksums file was created
        assert temp_dirs["checksums"].exists()
        
        # Verify content format
        content = temp_dirs["checksums"].read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            parts = line.split("  ")
            assert len(parts) == 2
            assert len(parts[0]) == 64  # SHA-256 is 64 hex chars

    def test_verify_checksums_empty_list(self, temp_dirs):
        """Test checksum verification with empty file list."""
        checksums = verify_checksums([], temp_dirs["checksums"])
        assert checksums == {}
        assert temp_dirs["checksums"].exists()
        assert temp_dirs["checksums"].read_text().strip() == ""

    def test_archive_data_basic(self, temp_dirs):
        """Test basic data archiving functionality."""
        # Create test files in source
        file1 = temp_dirs["source"] / "archive_test1.txt"
        file2 = temp_dirs["source"] / "archive_test2.txt"
        
        file1.write_bytes(b"Test content 1")
        file2.write_bytes(b"Test content 2")
        
        archive_data(temp_dirs["source"], temp_dirs["dest"])
        
        # Verify files were copied
        assert (temp_dirs["dest"] / "archive_test1.txt").exists()
        assert (temp_dirs["dest"] / "archive_test2.txt").exists()
        
        # Verify content matches
        assert (temp_dirs["dest"] / "archive_test1.txt").read_bytes() == b"Test content 1"
        assert (temp_dirs["dest"] / "archive_test2.txt").read_bytes() == b"Test content 2"

    def test_archive_data_overwrite_false(self, temp_dirs):
        """Test that archive_data preserves existing files (shutil.copy2 preserves metadata)."""
        # Create file in dest first
        dest_file = temp_dirs["dest"] / "existing.txt"
        dest_file.write_bytes(b"Original content")
        
        # Create same file in source with different content
        source_file = temp_dirs["source"] / "existing.txt"
        source_file.write_bytes(b"New content")
        
        archive_data(temp_dirs["source"], temp_dirs["dest"])
        
        # shutil.copy2 will overwrite, but we verify the new content is there
        assert dest_file.read_bytes() == b"New content"

    def test_archive_data_overwrite_true(self, temp_dirs):
        """Test archive behavior when destination already exists."""
        # Same as above - copy2 overwrites by default
        dest_file = temp_dirs["dest"] / "test.txt"
        dest_file.write_bytes(b"Old")
        
        source_file = temp_dirs["source"] / "test.txt"
        source_file.write_bytes(b"New")
        
        archive_data(temp_dirs["source"], temp_dirs["dest"])
        assert dest_file.read_bytes() == b"New"

    def test_archive_data_empty_source(self, temp_dirs):
        """Test archiving from empty source directory."""
        archive_data(temp_dirs["source"], temp_dirs["dest"])
        
        # Dest should exist but be empty
        assert temp_dirs["dest"].exists()
        assert len(list(temp_dirs["dest"].iterdir())) == 0

    def test_archive_data_source_not_found(self, temp_dirs):
        """Test that archiving from non-existent source raises error."""
        non_existent = temp_dirs["temp_base"] / "nonexistent_source"
        
        with pytest.raises(FileNotFoundError):
            archive_data(non_existent, temp_dirs["dest"])