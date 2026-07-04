"""
Unit tests for dataset download functionality.
Tests URL validation, checksum verification, and download logic.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.datasets.download_datasets import (
    validate_url_format,
    validate_dataset_id,
    compute_file_checksum,
    verify_checksum,
    DownloadError
)


class TestURLValidation:
    """Tests for URL format validation."""

    def test_valid_openneuro_url(self):
        """Test that valid OpenNeuro URLs are accepted."""
        valid_urls = [
            "https://openneuro.org/datasets/ds000001",
            "https://openneuro.org/datasets/ds001234",
            "https://openneuro.org/datasets/ds000001"
        ]
        
        for url in valid_urls:
            assert validate_url_format(url) is True

    def test_invalid_url_formats(self):
        """Test that invalid URL formats are rejected."""
        invalid_urls = [
            "http://openneuro.org/datasets/ds000001",  # http instead of https
            "https://openneuro.org/datasets/invalid",   # invalid ID format
            "https://example.com/datasets/ds000001",    # wrong domain
            "https://openneuro.org/",                   # missing dataset path
            "",                                          # empty string
            None,                                        # None value
            "not a url"                                 # plain text
        ]
        
        for url in invalid_urls:
            assert validate_url_format(url) is False


class TestDatasetIDValidation:
    """Tests for dataset ID validation."""

    def test_valid_dataset_ids(self):
        """Test that valid dataset IDs are accepted."""
        valid_ids = [
            "ds000001",
            "ds001234",
            "ds999999"
        ]
        
        for dataset_id in valid_ids:
            assert validate_dataset_id(dataset_id) is True

    def test_invalid_dataset_ids(self):
        """Test that invalid dataset IDs are rejected."""
        invalid_ids = [
            "ds00001",     # 5 digits instead of 6
            "ds0000001",   # 7 digits
            "DS000001",    # uppercase
            "ds00000a",    # non-numeric
            "000001",      # missing 'ds' prefix
            "ds123",       # too short
            "",            # empty string
            None           # None value
        ]
        
        for dataset_id in invalid_ids:
            assert validate_dataset_id(dataset_id) is False


class TestChecksumFunctions:
    """Tests for checksum computation and verification."""

    def test_compute_file_checksum(self):
        """Test checksum computation on a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Hello, World!")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 produces 64 hex characters
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_match(self):
        """Test checksum verification when values match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert verify_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test checksum verification when values don't match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            assert verify_checksum(temp_path, "wrong_checksum") is False
        finally:
            os.unlink(temp_path)

    def test_verify_nonexistent_file(self):
        """Test checksum verification on a non-existent file."""
        fake_path = Path("/nonexistent/file.txt")
        assert verify_checksum(fake_path, "any_checksum") is False


class TestDownloadError:
    """Tests for custom exception."""

    def test_download_error_message(self):
        """Test that DownloadError carries the correct message."""
        error = DownloadError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {
        'OPENNEURO_API_KEY': 'test_key',
        'DATA_DIR': '/tmp/test_data'
    }):
        yield


@pytest.fixture
def mock_openneuro_client():
    """Fixture to mock OpenNeuro client."""
    with patch('src.datasets.download_datasets.OpenNeuroClient') as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_dataset_info.return_value = {
            'id': 'ds000001',
            'created': '2023-01-01',
            'modified': '2023-01-02'
        }
        mock_client.return_value = mock_instance
        yield mock_client