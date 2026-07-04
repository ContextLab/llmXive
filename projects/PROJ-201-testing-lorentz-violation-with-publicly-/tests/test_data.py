"""
Tests for data acquisition and pre-processing pipeline.
Focus: US1 - Data Acquisition and Pre-processing.
"""
import os
import hashlib
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test (or the module if the function is internal)
# Based on task description, we are verifying checksum logic.
# We assume the logic resides in code/data/downloader.py or a utility.
# Since the implementation of downloader.py (T024) is not yet done,
# we implement the test logic here and ensure it can be run against
# a mock or the actual implementation once T024 is complete.
# However, per T021 description, we must verify `assert file_hash == expected_hash`.
# We will implement a helper function in the test file that mimics the verification
# logic expected in the downloader, or import it if it exists.
# Given T024 is not done, we cannot import from code.data.downloader.
# We will implement the verification logic locally for the test to validate the
# algorithmic correctness of the checksum check, which is the core of this task.

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify file integrity against expected hash.
    Returns True if match, raises AssertionError otherwise.
    """
    file_hash = compute_sha256(file_path)
    assert file_hash == expected_hash, f"Checksum mismatch: {file_hash} != {expected_hash}"
    return True

class TestChecksumVerification:
    """Tests for checksum verification logic (T021)."""

    @pytest.fixture
    def temp_file(self, tmp_path: Path):
        """Create a temporary file with known content."""
        file_path = tmp_path / "test_map.fits"
        content = b"SMICA_TT_Nside2048_MockData_v1"
        file_path.write_bytes(content)
        return str(file_path), hashlib.sha256(content).hexdigest()

    def test_checksum_verification(self, temp_file):
        """
        Verify `assert file_hash == expected_hash` logic.
        T021: Unit test tests/test_data.py::test_checksum_verification
        """
        file_path, expected_hash = temp_file
        
        # This should pass
        verify_checksum(file_path, expected_hash)

    def test_checksum_verification_failure(self, temp_file):
        """
        Verify that checksum mismatch raises an assertion error.
        """
        file_path, _ = temp_file
        wrong_hash = "0" * 64  # Invalid hash

        with pytest.raises(AssertionError):
            verify_checksum(file_path, wrong_hash)

    def test_checksum_verification_real_data_simulation(self, tmp_path: Path):
        """
        Simulate a realistic scenario where a file is downloaded and verified.
        """
        # Create a file that simulates a downloaded FITS header + data
        file_path = tmp_path / "plk_smica_tT.fits"
        # Mock FITS-like binary content
        content = b"\x00\x01\x02SIMPLE  =                    T / file does conform to FITS standard             BITPIX  =                    8 / number of bits per data pixel                  NAXIS   =                    0 / number of data axes                            END" + b"\x00" * 1000
        file_path.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()

        # Verify
        verify_checksum(str(file_path), expected_hash)

        # Verify with slightly modified content (corrupted download)
        corrupted_content = content + b"corruption"
        corrupted_path = tmp_path / "corrupted.fits"
        corrupted_path.write_bytes(corrupted_content)
        
        with pytest.raises(AssertionError):
            verify_checksum(str(corrupted_path), expected_hash)
