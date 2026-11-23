import os
import tempfile
from pathlib import Path
import pytest

# Import the functions from the module under test
from code.utils.checksum import calculate_md5, calculate_sha256, verify_checksum, validate_input_file

class TestChecksumUtilities:
    """Unit tests for checksum utilities."""

    def test_calculate_md5_existing_file(self, tmp_path):
        """Test MD5 calculation on an existing file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        md5_hash = calculate_md5(test_file)
        # Pre-calculated MD5 for "Hello, World!"
        expected_md5 = "65a8e27d8879283831b664bd8b7f0ad4"
        
        assert md5_hash == expected_md5

    def test_calculate_sha256_existing_file(self, tmp_path):
        """Test SHA256 calculation on an existing file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        sha256_hash = calculate_sha256(test_file)
        # Pre-calculated SHA256 for "Hello, World!"
        expected_sha256 = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        assert sha256_hash == expected_sha256

    def test_calculate_checksum_missing_file(self):
        """Test that calculating checksum on a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_md5("/nonexistent/path/file.txt")
        
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

    def test_verify_checksum_match(self, tmp_path):
        """Test checksum verification when values match."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        actual_md5 = calculate_md5(test_file)
        assert verify_checksum(test_file, actual_md5, "md5") is True
        
        actual_sha256 = calculate_sha256(test_file)
        assert verify_checksum(test_file, actual_sha256, "sha256") is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification when values do not match."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        wrong_checksum = "0" * 32  # Invalid MD5
        assert verify_checksum(test_file, wrong_checksum, "md5") is False

    def test_verify_checksum_invalid_algorithm(self, tmp_path):
        """Test that an invalid algorithm raises ValueError."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        with pytest.raises(ValueError):
            verify_checksum(test_file, "some_hash", "invalid_algo")

    def test_validate_input_file_exists(self, tmp_path):
        """Test validation of an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        is_valid, error = validate_input_file(test_file)
        assert is_valid is True
        assert error is None

    def test_validate_input_file_missing(self):
        """Test validation of a missing file."""
        is_valid, error = validate_input_file("/nonexistent/file.txt")
        assert is_valid is False
        assert "File not found" in error

    def test_validate_input_file_checksum_match(self, tmp_path):
        """Test validation with matching checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        expected_md5 = calculate_md5(test_file)
        is_valid, error = validate_input_file(test_file, required_checksum=expected_md5)
        
        assert is_valid is True
        assert error is None

    def test_validate_input_file_checksum_mismatch(self, tmp_path):
        """Test validation with mismatched checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        is_valid, error = validate_input_file(test_file, required_checksum="invalid_hash")
        
        assert is_valid is False
        assert "Checksum mismatch" in error