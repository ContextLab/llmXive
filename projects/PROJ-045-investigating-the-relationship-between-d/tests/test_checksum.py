"""
Tests for the SHA-256 checksumming utility in code/utils.py.
"""
import hashlib
import os
import tempfile
from pathlib import Path

import pytest

# Import the function to test
# Assuming the test runs from the project root where 'code' is a package or module path
# We adjust sys.path if necessary, but typically in pytest setup this is handled.
# For this standalone snippet, we assume 'code' is in the path.
import sys
from pathlib import Path

# Ensure we can import from code/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import compute_file_checksum, verify_checksum


class TestChecksumUtilities:
    """Test cases for checksum functions."""

    def setup_method(self):
        """Create a temporary file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = Path(self.temp_dir) / "test_data.txt"
        self.test_content = b"Hello, llmXive research pipeline! This is a test file for checksumming."
        self.test_file_path.write_bytes(self.test_content)

    def teardown_method(self):
        """Clean up temporary files."""
        if self.test_file_path.exists():
            self.test_file_path.unlink()
        if Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()

    def test_compute_sha256(self):
        """Test that compute_file_checksum returns the correct SHA-256 hash."""
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(self.test_content).hexdigest()

        result = compute_file_checksum(str(self.test_file_path), algorithm="sha256")

        assert result == expected_hash
        assert len(result) == 64  # SHA-256 hex length

    def test_compute_md5(self):
        """Test that compute_file_checksum works with MD5."""
        expected_hash = hashlib.md5(self.test_content).hexdigest()

        result = compute_file_checksum(str(self.test_file_path), algorithm="md5")

        assert result == expected_hash
        assert len(result) == 32  # MD5 hex length

    def test_verify_checksum_success(self):
        """Test verify_checksum returns True for matching checksums."""
        checksum = compute_file_checksum(str(self.test_file_path), algorithm="sha256")

        assert verify_checksum(str(self.test_file_path), checksum, algorithm="sha256") is True

    def test_verify_checksum_failure(self):
        """Test verify_checksum returns False for mismatched checksums."""
        wrong_checksum = "a" * 64

        assert verify_checksum(str(self.test_file_path), wrong_checksum, algorithm="sha256") is False

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/non/existent/file.txt")

        with pytest.raises(FileNotFoundError):
            verify_checksum("/non/existent/file.txt", "somehash")

    def test_invalid_algorithm(self):
        """Test that ValueError is raised for unsupported algorithms."""
        with pytest.raises(ValueError, match="Unsupported hash algorithm"):
            compute_file_checksum(str(self.test_file_path), algorithm="blake2b")

    def test_large_file_handling(self):
        """Test checksumming a larger file to ensure chunking works."""
        large_file_path = Path(self.temp_dir) / "large_file.bin"
        # Create a 1MB file
        content = os.urandom(1024 * 1024)
        large_file_path.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()

        result = compute_file_checksum(str(large_file_path), chunk_size=4096)

        assert result == expected_hash
        large_file_path.unlink()

    def test_case_insensitive_verification(self):
        """Test that verify_checksum is case-insensitive regarding the expected hash."""
        checksum = compute_file_checksum(str(self.test_file_path), algorithm="sha256")
        upper_checksum = checksum.upper()

        assert verify_checksum(str(self.test_file_path), upper_checksum, algorithm="sha256") is True
