"""
Tests for the error handling module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from data.error_handler import (
    DataCorruptionError,
    DownloadFailureError,
    verify_file_integrity,
    handle_download_failure,
    validate_environment_constraints
)
from data.download import download_dataset

class TestErrorHandler:
    def test_verify_file_integrity_success(self, tmp_path):
        """Test successful verification of a file with correct checksum."""
        content = b"test data for integrity"
        file_path = tmp_path / "test_file.txt"
        file_path.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Should not raise
        result = verify_file_integrity(file_path, expected_hash)
        assert result is True

    def test_verify_file_integrity_mismatch(self, tmp_path):
        """Test that DataCorruptionError is raised on checksum mismatch."""
        content = b"test data"
        file_path = tmp_path / "test_file.txt"
        file_path.write_bytes(content)
        
        wrong_hash = "a" * 64
        
        with pytest.raises(DataCorruptionError):
            verify_file_integrity(file_path, wrong_hash)

    def test_verify_file_integrity_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised if file is missing."""
        file_path = tmp_path / "non_existent.txt"
        
        with pytest.raises(FileNotFoundError):
            verify_file_integrity(file_path, "some_hash")

    def test_handle_download_failure(self):
        """Test that handle_download_failure raises DownloadFailureError."""
        error = ConnectionError("Network unreachable")
        url = "http://example.com/data"
        
        with pytest.raises(DownloadFailureError) as exc_info:
            handle_download_failure(error, url)
        
        assert "DOWNLOAD FAILURE" in str(exc_info.value)
        assert url in str(exc_info.value)

    @patch('data.error_handler.os.getenv')
    def test_validate_environment_constraints_cpu_only(self, mock_getenv):
        """Test that validation passes in CPU-only environment."""
        mock_getenv.side_effect = lambda key, default="": default
        # Should not raise
        validate_environment_constraints()

    @patch('data.error_handler.os.getenv')
    def test_validate_environment_constraints_gpu_forced(self, mock_getenv):
        """Test that validation fails if GPU is forced."""
        def side_effect(key, default=""):
            if key == "LLMXIVE_FORCE_GPU":
                return "true"
            return default
        
        mock_getenv.side_effect = side_effect
        
        with pytest.raises(Exception): # ConfigurationError
            validate_environment_constraints()

    @patch('data.error_handler.os.getenv')
    def test_validate_environment_constraints_quantization_forced(self, mock_getenv):
        """Test that validation fails if quantization is forced."""
        def side_effect(key, default=""):
            if key == "LLMXIVE_FORCE_QUANTIZATION":
                return "true"
            return default
        
        mock_getenv.side_effect = side_effect
        
        with pytest.raises(Exception): # ConfigurationError
            validate_environment_constraints()