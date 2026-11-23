"""
Unit tests for code/utils/data_fetchers.py
"""
import pytest
from code.utils.data_fetchers import DataFetchError, calculate_sha256
import tempfile
import os


class TestCalculateSha256:
    def test_calculate_sha256_known_file(self):
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            # Calculate hash of the file
            hash_value = calculate_sha256(temp_path)
            # Expected SHA256 of "Hello, World!"
            expected_hash = "d90a980e2e87a06939575d8a3e884076d72e2838660d7c87263e5d2989755346"
            assert hash_value == expected_hash
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256_empty_file(self):
        # Create a temporary empty file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            hash_value = calculate_sha256(temp_path)
            # Expected SHA256 of empty string
            expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495992b04599939"
            assert hash_value == expected_hash
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

class TestDataFetchError:
    def test_datafetcherror_creation(self):
        error = DataFetchError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_datafetcherror_with_code(self):
        error = DataFetchError("Network error", code=404)
        assert "Network error" in str(error)
        # The error object should be usable as an exception
