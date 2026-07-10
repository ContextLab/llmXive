"""
Unit tests for the state manager module.
Tests SHA-256 calculation and state file operations.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.state_manager import calculate_sha256, update_artifact_checksums


class TestSHA256Calculation:
    """Tests for SHA-256 hash calculation."""

    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        hash_result = calculate_sha256(test_file)
        
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected

    def test_calculate_sha256_simple_content(self, tmp_path):
        """Test hashing a file with simple content."""
        test_file = tmp_path / "content.txt"
        test_file.write_text("Hello, World!")
        
        hash_result = calculate_sha256(test_file)
        
        # Known SHA-256 for "Hello, World!"
        expected = "c0535e4b270c2d0d0e4e5b4b8b1b4b1b4b1b4b1b4b1b4b1b4b1b4b1b4b1b4b1b"
        # Actually calculate it to be sure
        import hashlib
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        
        assert hash_result == expected

    def test_calculate_sha256_nonexistent_file(self, tmp_path):
        """Test hashing a non-existent file returns None."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        hash_result = calculate_sha256(nonexistent)
        
        assert hash_result is None


class TestArtifactChecksums:
    """Tests for artifact checksum calculation."""

    def test_update_artifact_checksums_multiple_files(self, tmp_path):
        """Test calculating checksums for multiple files."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        
        # Calculate checksums
        rel_paths = [
            str(file1.relative_to(tmp_path)),
            str(file2.relative_to(tmp_path))
        ]
        
        # Temporarily change project root for testing
        import utils.state_manager as sm
        original_root = sm.PROJECT_ROOT
        sm.PROJECT_ROOT = tmp_path
        
        try:
            checksums = update_artifact_checksums(rel_paths)
            
            assert len(checksums) == 2
            assert str(file1.relative_to(tmp_path)) in checksums
            assert str(file2.relative_to(tmp_path)) in checksums
            
            # Verify hashes are valid SHA-256
            for path, hash_val in checksums.items():
                assert len(hash_val) == 64  # SHA-256 hex length
                assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            sm.PROJECT_ROOT = original_root

    def test_update_artifact_checksums_missing_file(self, tmp_path):
        """Test handling of missing files in checksum calculation."""
        rel_paths = ["missing.txt", "existing.txt"]
        
        # Create only one file
        existing = tmp_path / "existing.txt"
        existing.write_text("Exists")
        
        import utils.state_manager as sm
        original_root = sm.PROJECT_ROOT
        sm.PROJECT_ROOT = tmp_path
        
        try:
            checksums = update_artifact_checksums(rel_paths)
            
            # Should only contain the existing file
            assert len(checksums) == 1
            assert "existing.txt" in checksums
            assert "missing.txt" not in checksums
        finally:
            sm.PROJECT_ROOT = original_root
