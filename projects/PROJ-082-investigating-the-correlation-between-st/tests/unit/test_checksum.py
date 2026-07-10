"""
Unit tests for data hygiene utilities (checksum.py).
"""

import hashlib
import tempfile
import os
from pathlib import Path
import pytest

from code.utils.checksum import (
    calculate_md5,
    calculate_sha256,
    verify_checksum,
    validate_input_file
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content for testing."""
    content = b"Test data for checksum validation."
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path, content
    os.unlink(temp_path)


@pytest.fixture
def empty_file():
    """Create an empty temporary file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestCalculateMD5:
    def test_calculate_md5_known_value(self, temp_file):
        """Test MD5 calculation against a known value."""
        file_path, content = temp_file
        expected_md5 = hashlib.md5(content).hexdigest()
        result = calculate_md5(file_path)
        assert result == expected_md5

    def test_calculate_md5_empty_file(self, empty_file):
        """Test MD5 calculation on an empty file."""
        expected_md5 = hashlib.md5(b"").hexdigest()
        result = calculate_md5(empty_file)
        assert result == expected_md5

    def test_calculate_md5_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_md5("/nonexistent/path/file.txt")


class TestCalculateSHA256:
    def test_calculate_sha256_known_value(self, temp_file):
        """Test SHA256 calculation against a known value."""
        file_path, content = temp_file
        expected_sha256 = hashlib.sha256(content).hexdigest()
        result = calculate_sha256(file_path)
        assert result == expected_sha256

    def test_calculate_sha256_empty_file(self, empty_file):
        """Test SHA256 calculation on an empty file."""
        expected_sha256 = hashlib.sha256(b"").hexdigest()
        result = calculate_sha256(empty_file)
        assert result == expected_sha256

    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")


class TestVerifyChecksum:
    def test_verify_checksum_success(self, temp_file):
        """Test successful checksum verification."""
        file_path, content = temp_file
        expected_md5 = hashlib.md5(content).hexdigest()
        is_valid, calculated = verify_checksum(file_path, expected_md5, "md5")
        assert is_valid is True
        assert calculated == expected_md5

    def test_verify_checksum_failure(self, temp_file):
        """Test checksum verification failure with wrong expected value."""
        file_path, _ = temp_file
        is_valid, calculated = verify_checksum(file_path, "wrong_checksum", "md5")
        assert is_valid is False
        assert calculated != "wrong_checksum"

    def test_verify_checksum_file_not_found(self):
        """Test verification fails gracefully for missing file."""
        with pytest.raises(FileNotFoundError):
            verify_checksum("/nonexistent/file.txt", "abc123")

    def test_verify_checksum_invalid_algorithm(self, temp_file):
        """Test that ValueError is raised for unsupported algorithm."""
        file_path, _ = temp_file
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            verify_checksum(file_path, "abc123", "invalid_algo")


class TestValidateInputFile:
    def test_validate_input_file_success(self, temp_file):
        """Test successful validation with no expected checksums."""
        file_path, _ = temp_file
        result = validate_input_file(file_path)
        assert result["valid"] is True
        assert "md5" in result["checksums"]
        assert "sha256" in result["checksums"]
        assert len(result["errors"]) == 0

    def test_validate_input_file_with_matching_checksum(self, temp_file):
        """Test validation with matching expected checksums."""
        file_path, content = temp_file
        expected = {
            "md5": hashlib.md5(content).hexdigest(),
            "sha256": hashlib.sha256(content).hexdigest()
        }
        result = validate_input_file(file_path, expected)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_input_file_with_mismatched_checksum(self, temp_file):
        """Test validation with mismatched expected checksum."""
        file_path, _ = temp_file
        expected = {"md5": "wrong_checksum"}
        result = validate_input_file(file_path, expected)
        assert result["valid"] is False
        assert any("MD5 mismatch" in err for err in result["errors"])

    def test_validate_input_file_not_found(self):
        """Test validation for missing file."""
        result = validate_input_file("/nonexistent/file.txt")
        assert result["valid"] is False
        assert any("File not found" in err for err in result["errors"])
