"""
Unit tests for checksum verification functionality (T016).
"""
import os
import tempfile
import hashlib
import yaml
from pathlib import Path
import pytest

# Import the functions to test
from checksum_verification import (
    calculate_sha256,
    verify_sparc_data_integrity,
    update_metadata_with_verification
)

from utils import get_timestamp

class TestCalculateSha256:
    """Tests for the calculate_sha256 function."""

    def test_calculate_sha256_known_file(self, tmp_path):
        """Test SHA-256 calculation on a known file content."""
        # Create a test file with known content
        test_content = b"Hello, World!"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)

        # Calculate checksum
        checksum = calculate_sha256(test_file)

        # Verify against known SHA-256
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected

    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA-256 calculation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        checksum = calculate_sha256(test_file)
        expected = hashlib.sha256(b"").hexdigest()
        assert checksum == expected

    def test_calculate_sha256_large_file(self, tmp_path):
        """Test SHA-256 calculation on a larger file."""
        # Create a larger test file
        content = b"0123456789" * 10000  # 100KB
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(content)

        checksum = calculate_sha256(test_file)
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected


class TestVerifySparcDataIntegrity:
    """Tests for the verify_sparc_data_integrity function."""

    def test_verify_nonexistent_file(self, tmp_path):
        """Test verification of a non-existent file."""
        nonexistent = tmp_path / "does_not_exist.zip"
        result = verify_sparc_data_integrity(nonexistent)

        assert result["verified"] is False
        assert result["error"] == "File not found"
        assert result["path"] == str(nonexistent)

    def test_verify_file_without_expected_checksum(self, tmp_path):
        """Test verification when no expected checksum is provided."""
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(b"test content")

        result = verify_sparc_data_integrity(test_file)

        assert result["verified"] is True
        assert "checksum" in result
        assert "file_size" in result
        assert "file_mtime" in result

    def test_verify_file_matching_checksum(self, tmp_path):
        """Test verification when checksum matches expected."""
        test_content = b"matching content"
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(test_content)

        expected_checksum = hashlib.sha256(test_content).hexdigest()
        result = verify_sparc_data_integrity(test_file, expected_checksum)

        assert result["verified"] is True
        assert result["checksum"] == expected_checksum

    def test_verify_file_mismatched_checksum(self, tmp_path):
        """Test verification when checksum does not match expected."""
        test_content = b"mismatched content"
        test_file = tmp_path / "test.zip"
        test_file.write_bytes(test_content)

        wrong_checksum = "0" * 64  # Invalid checksum
        result = verify_sparc_data_integrity(test_file, wrong_checksum)

        assert result["verified"] is False
        assert result["error"] == "Checksum mismatch"


class TestUpdateMetadataWithVerification:
    """Tests for the update_metadata_with_verification function."""

    def test_update_existing_metadata(self, tmp_path):
        """Test updating an existing metadata file."""
        metadata_file = tmp_path / "metadata.yaml"
        
        # Create initial metadata
        initial_metadata = {
            "project": {"name": "test-project"},
            "data": {"source": "test"}
        }
        with open(metadata_file, 'w') as f:
            yaml.dump(initial_metadata, f)

        verification_result = {
            "verified": True,
            "checksum": "abc123",
            "file_size": 1024
        }

        success = update_metadata_with_verification(metadata_file, verification_result)

        assert success is True
        assert metadata_file.exists()

        # Verify the file was updated correctly
        with open(metadata_file, 'r') as f:
            updated_metadata = yaml.safe_load(f)

        assert "verification" in updated_metadata["data"]
        assert updated_metadata["data"]["verification"]["verified"] is True
        assert updated_metadata["data"]["verification"]["checksum"] == "abc123"

    def test_create_new_metadata(self, tmp_path):
        """Test creating a new metadata file when it doesn't exist."""
        metadata_file = tmp_path / "new_metadata.yaml"
        
        verification_result = {
            "verified": True,
            "checksum": "def456",
            "file_size": 2048
        }

        success = update_metadata_with_verification(metadata_file, verification_result)

        assert success is True
        assert metadata_file.exists()

        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f)

        assert "data" in metadata
        assert "verification" in metadata["data"]
        assert metadata["data"]["verification"]["verified"] is True

    def test_update_with_download_info(self, tmp_path):
        """Test updating metadata with download information."""
        metadata_file = tmp_path / "metadata.yaml"
        
        verification_result = {
            "verified": True,
            "checksum": "ghi789"
        }

        download_info = {
            "timestamp": "2024-01-01T00:00:00",
            "version": "2.0"
        }

        success = update_metadata_with_verification(metadata_file, verification_result, download_info)

        assert success is True

        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f)

        assert metadata["data"]["download_timestamp"] == "2024-01-01T00:00:00"
        assert metadata["data"]["version"] == "2.0"

    def test_update_failed_verification(self, tmp_path):
        """Test updating metadata with a failed verification result."""
        metadata_file = tmp_path / "metadata.yaml"
        
        verification_result = {
            "verified": False,
            "error": "Checksum mismatch",
            "checksum": "wrong"
        }

        success = update_metadata_with_verification(metadata_file, verification_result)

        assert success is True

        with open(metadata_file, 'r') as f:
            metadata = yaml.safe_load(f)

        assert metadata["data"]["verification"]["verified"] is False
        assert metadata["data"]["verification"]["error"] == "Checksum mismatch"
