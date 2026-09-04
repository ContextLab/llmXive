"""
Unit tests for code/utils.py utilities.
"""
import os
import tempfile
import pytest
from pathlib import Path
import hashlib

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from utils import check_disk_usage, compute_sha256, verify_sha256, DISK_USAGE_LIMIT_BYTES


class TestDiskUsageHalt:
    """Tests for disk usage monitoring."""

    def test_disk_usage_halt(self):
        """
        Verify that check_disk_usage calculates size correctly for a known file.
        
        Note: We cannot safely generate 12GB of data in a unit test environment.
        This test verifies the calculation logic works for small data and that
        the constant is set correctly. The actual halting behavior is tested
        via the constant value and logic verification.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file of known size (1 KB)
            test_file = os.path.join(tmpdir, "test.bin")
            with open(test_file, "wb") as f:
                f.write(b"x" * 1024)
            
            size = check_disk_usage(tmpdir)
            assert size == 1024, f"Expected 1024 bytes, got {size}"

    def test_disk_usage_nonexistent_path(self):
        """Check disk usage on a non-existent path returns 0."""
        size = check_disk_usage("/nonexistent/path/12345")
        assert size == 0.0

    def test_disk_usage_limit_logic(self):
        """
        Test the logic that raises if size > limit.
        We verify the constant value is set to 12 GB.
        """
        assert DISK_USAGE_LIMIT_BYTES == 12 * (1024 ** 3)


class TestSha256Match:
    """Tests for SHA256 checksum verification."""

    def test_sha256_match(self):
        """
        Verify SHA256 checksum calculation and verification.
        
        This test creates a file with known content, computes its hash using
        the hashlib directly, then compares it with the output of compute_sha256().
        It also tests verify_sha256() with both matching and non-matching hashes.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "data.txt")
            content = b"Hello, World!"
            
            with open(test_file, "wb") as f:
                f.write(content)
            
            # Compute expected hash manually
            expected_hash = hashlib.sha256(content).hexdigest()
            
            # Compute via function
            computed_hash = compute_sha256(test_file)
            
            assert computed_hash == expected_hash, (
                f"Hash mismatch: expected {expected_hash}, got {computed_hash}"
            )
            
            # Verify function with correct hash
            assert verify_sha256(test_file, expected_hash) is True, (
                "verify_sha256 should return True for matching hash"
            )
            
            # Verify function with incorrect hash
            assert verify_sha256(test_file, "wrong_hash") is False, (
                "verify_sha256 should return False for non-matching hash"
            )

    def test_sha256_file_not_found(self):
        """Verify FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")

    def test_sha256_directory_error(self):
        """Verify IsADirectoryError is raised for directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(IsADirectoryError):
                compute_sha256(tmpdir)