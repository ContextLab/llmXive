"""
Unit tests for dataset download functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.datasets.download_datasets import (
    validate_url_format,
    get_dataset_id_from_url,
    compute_file_checksum,
    verify_checksum,
    download_dataset,
    download_datasets_from_list,
    DownloadError,
    URLValidationError,
    ChecksumError
)


class TestURLValidation:
    """Tests for URL validation functions."""

    def test_valid_openneuro_url(self):
        """Test valid OpenNeuro URL format."""
        url = "https://openneuro.org/datasets/ds000001"
        is_valid, error = validate_url_format(url)
        assert is_valid is True
        assert error == ""

    def test_invalid_url_no_scheme(self):
        """Test URL without scheme."""
        url = "openneuro.org/datasets/ds000001"
        is_valid, error = validate_url_format(url)
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_invalid_url_wrong_domain(self):
        """Test URL from wrong domain."""
        url = "https://example.com/datasets/ds000001"
        is_valid, error = validate_url_format(url)
        assert is_valid is False
        assert "openneuro.org" in error

    def test_invalid_url_no_dataset_id(self):
        """Test URL without valid dataset ID."""
        url = "https://openneuro.org/datasets/invalid"
        is_valid, error = validate_url_format(url)
        assert is_valid is False
        assert "dataset ID" in error

    def test_empty_url(self):
        """Test empty URL."""
        url = ""
        is_valid, error = validate_url_format(url)
        assert is_valid is False
        assert "non-empty string" in error

    def test_none_url(self):
        """Test None URL."""
        url = None
        is_valid, error = validate_url_format(url)
        assert is_valid is False


class TestDatasetIDExtraction:
    """Tests for dataset ID extraction."""

    def test_extract_valid_id(self):
        """Test extraction of valid dataset ID."""
        url = "https://openneuro.org/datasets/ds000001/files"
        dataset_id = get_dataset_id_from_url(url)
        assert dataset_id == "ds000001"

    def test_extract_id_from_complex_url(self):
        """Test extraction from complex URL."""
        url = "https://openneuro.org/datasets/ds001234/versions/1.0.0"
        dataset_id = get_dataset_id_from_url(url)
        assert dataset_id == "ds001234"

    def test_extract_invalid_id(self):
        """Test extraction from invalid URL."""
        url = "https://example.com/not-a-dataset"
        dataset_id = get_dataset_id_from_url(url)
        assert dataset_id is None


class TestChecksumFunctions:
    """Tests for checksum computation and verification."""

    def test_compute_checksum(self):
        """Test checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_match(self):
        """Test checksum verification with matching checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            assert verify_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test checksum verification with mismatched checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            wrong_checksum = "a" * 64
            assert verify_checksum(temp_path, wrong_checksum) is False
        finally:
            os.unlink(temp_path)


class TestDownloadDataset:
    """Tests for dataset download functionality."""

    @patch('src.datasets.download_datasets.create_client')
    @patch('src.datasets.download_datasets.download_file')
    def test_download_dataset_success(self, mock_download_file, mock_create_client):
        """Test successful dataset download."""
        # Mock the client
        mock_client = MagicMock()
        mock_client.get_dataset_info.return_value = {
            'id': 'ds000001',
            'checksum': 'abc123'
        }
        mock_create_client.return_value = mock_client

        # Mock download_file to not actually download
        mock_download_file.side_effect = None

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = download_dataset('ds000001', output_dir)

            assert result['dataset_id'] == 'ds000001'
            assert result['status'] in ['success', 'partial']
            assert result['output_dir'] == str(output_dir / 'ds000001')

    def test_download_dataset_invalid_id(self):
        """Test download with invalid dataset ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with pytest.raises(URLValidationError):
                download_dataset('invalid_id', output_dir)

    @patch('src.datasets.download_datasets.create_client')
    def test_download_dataset_api_error(self, mock_create_client):
        """Test download when API fails."""
        mock_client = MagicMock()
        mock_client.get_dataset_info.side_effect = Exception("API error")
        mock_create_client.return_value = mock_client

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            with pytest.raises(DownloadError):
                download_dataset('ds000001', output_dir)


class TestDownloadDatasetsFromList:
    """Tests for batch download functionality."""

    @patch('src.datasets.download_datasets.download_dataset')
    def test_download_multiple_datasets(self, mock_download_dataset):
        """Test downloading multiple datasets."""
        # Mock successful downloads
        mock_download_dataset.side_effect = [
            {'dataset_id': 'ds000001', 'status': 'success', 'output_dir': '/tmp/ds000001'},
            {'dataset_id': 'ds000002', 'status': 'success', 'output_dir': '/tmp/ds000002'}
        ]

        results = download_datasets_from_list(['ds000001', 'ds000002'])

        assert len(results) == 2
        assert all(r['status'] == 'success' for r in results)

    @patch('src.datasets.download_datasets.download_dataset')
    def test_download_with_failures(self, mock_download_dataset):
        """Test downloading with some failures."""
        from src.datasets.download_datasets import DownloadError

        def side_effect(dataset_id, output_dir):
            if dataset_id == 'ds000001':
                return {'dataset_id': dataset_id, 'status': 'success', 'output_dir': '/tmp/ds000001'}
            else:
                raise DownloadError("Simulated error")

        mock_download_dataset.side_effect = side_effect

        results = download_datasets_from_list(['ds000001', 'ds000002'])

        assert len(results) == 2
        assert results[0]['status'] == 'success'
        assert results[1]['status'] == 'failed'
        assert 'error' in results[1]