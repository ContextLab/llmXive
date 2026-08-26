"""
Tests for checksum utility functions.
"""
import pytest
import os
import tempfile
import hashlib
from utils.checksum import compute_file_hash, compute_directory_hash

class TestChecksum:
    def test_compute_file_hash(self):
        """Test file hash computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Compute expected hash
            expected_hash = hashlib.sha256(b"test content").hexdigest()

            # Compute actual hash
            actual_hash = compute_file_hash(temp_path)

            assert actual_hash == expected_hash
        finally:
            os.unlink(temp_path)

    def test_compute_file_hash_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash("/nonexistent/file.txt")

    def test_compute_directory_hash(self):
        """Test directory hash computation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.txt")
            file2 = os.path.join(temp_dir, "file2.txt")

            with open(file1, 'w') as f:
                f.write("content1")
            with open(file2, 'w') as f:
                f.write("content2")

            # Compute directory hash
            dir_hash = compute_directory_hash(temp_dir)

            # Should be a valid hex string
            assert len(dir_hash) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in dir_hash)

    def test_compute_directory_hash_empty(self):
        """Test directory hash with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_hash = compute_directory_hash(temp_dir)
            assert len(dir_hash) == 64

    def test_compute_directory_hash_nonexistent(self):
        """Test that NotADirectoryError is raised for non-existent directories."""
        with pytest.raises(NotADirectoryError):
            compute_directory_hash("/nonexistent/directory")
