import os
import tempfile
import pytest
from pathlib import Path
from code.utils.checksum import calculate_md5, calculate_sha256, verify_checksum, validate_input_file

class TestChecksumUtilities:
    """Unit tests for data hygiene checksum utilities."""

    def test_calculate_md5(self):
        """Test MD5 calculation on a known string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name
        
        try:
            # "Hello, World!" MD5 is 65a8e27d8879283831b664bd8b7f0ad4
            expected_md5 = "65a8e27d8879283831b664bd8b7f0ad4"
            actual_md5 = calculate_md5(temp_path)
            assert actual_md5 == expected_md5, f"Expected {expected_md5}, got {actual_md5}"
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name
        
        try:
            # "Hello, World!" SHA256 is dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
            expected_sha256 = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            actual_sha256 = calculate_sha256(temp_path)
            assert actual_sha256 == expected_sha256, f"Expected {expected_sha256}, got {actual_sha256}"
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_md5(self):
        """Test checksum verification with matching MD5."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test Data")
            temp_path = f.name
        
        try:
            # Calculate real checksum first
            real_checksum = calculate_md5(temp_path)
            assert verify_checksum(temp_path, real_checksum, "md5") is True
            assert verify_checksum(temp_path, "wrong_checksum", "md5") is False
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_sha256(self):
        """Test checksum verification with matching SHA256."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test Data")
            temp_path = f.name
        
        try:
            real_checksum = calculate_sha256(temp_path)
            assert verify_checksum(temp_path, real_checksum, "sha256") is True
            assert verify_checksum(temp_path, "wrong_checksum", "sha256") is False
        finally:
            os.unlink(temp_path)

    def test_validate_input_file_exists(self):
        """Test validation of an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Valid file")
            temp_path = f.name
        
        try:
            is_valid, error = validate_input_file(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_validate_input_file_not_found(self):
        """Test validation of a non-existent file."""
        is_valid, error = validate_input_file("/nonexistent/path/file.txt")
        assert is_valid is False
        assert "not found" in error.lower()

    def test_validate_input_file_checksum_mismatch(self):
        """Test validation with incorrect checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Data")
            temp_path = f.name
        
        try:
            is_valid, error = validate_input_file(temp_path, required_checksum="invalid_checksum")
            assert is_valid is False
            assert "mismatch" in error.lower()
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_case_insensitive(self):
        """Test that checksum verification is case insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Case Test")
            temp_path = f.name
        
        try:
            real_checksum = calculate_md5(temp_path)
            upper_checksum = real_checksum.upper()
            lower_checksum = real_checksum.lower()
            
            assert verify_checksum(temp_path, upper_checksum) is True
            assert verify_checksum(temp_path, lower_checksum) is True
        finally:
            os.unlink(temp_path)

    def test_unsupported_algorithm(self):
        """Test that unsupported algorithm raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Data")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported algorithm"):
                verify_checksum(temp_path, "some_checksum", algorithm="blake2")
        finally:
            os.unlink(temp_path)
