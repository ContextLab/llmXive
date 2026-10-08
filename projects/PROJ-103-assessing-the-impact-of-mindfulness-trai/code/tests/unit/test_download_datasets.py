"""
Unit tests for download_datasets module.

Tests URL validation, checksum functions, and download functionality.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.datasets.download_datasets import (
    DownloadError,
    URLValidationError,
    ChecksumError,
    validate_url_format,
    get_dataset_id_from_url,
    compute_file_checksum,
    verify_checksum,
    download_file,
    download_dataset,
    download_datasets_from_list
)


class TestURLValidation:
    """Tests for URL validation functions."""
    
    def test_valid_openneuro_url(self):
        """Test that valid OpenNeuro URLs pass validation."""
        valid_urls = [
            "https://openneuro.org/datasets/ds000001",
            "https://openneuro.org/datasets/ds000001/files",
            "https://openneuro.org/datasets/ds000001/versions/1.0.0"
        ]
        
        for url in valid_urls:
            assert validate_url_format(url) is True
    
    def test_invalid_scheme(self):
        """Test that URLs with invalid schemes fail validation."""
        invalid_urls = [
            "ftp://openneuro.org/datasets/ds000001",
            "file:///openneuro.org/datasets/ds000001",
            "openneuro.org/datasets/ds000001"
        ]
        
        for url in invalid_urls:
            with pytest.raises(URLValidationError):
                validate_url_format(url)
    
    def test_invalid_domain(self):
        """Test that URLs with invalid domains fail validation."""
        invalid_urls = [
            "https://example.com/datasets/ds000001",
            "https://openneuro.example.org/datasets/ds000001"
        ]
        
        for url in invalid_urls:
            with pytest.raises(URLValidationError):
                validate_url_format(url)
    
    def test_missing_datasets_path(self):
        """Test that URLs missing /datasets/ path fail validation."""
        invalid_urls = [
            "https://openneuro.org/ds000001",
            "https://openneuro.org/files/ds000001"
        ]
        
        for url in invalid_urls:
            with pytest.raises(URLValidationError):
                validate_url_format(url)
    
    def test_empty_url(self):
        """Test that empty URLs fail validation."""
        with pytest.raises(URLValidationError):
            validate_url_format("")
        
        with pytest.raises(URLValidationError):
            validate_url_format(None)
    
    def test_non_string_url(self):
        """Test that non-string URLs fail validation."""
        with pytest.raises(URLValidationError):
            validate_url_format(123)
    
    def test_invalid_dataset_id_in_url(self):
        """Test that URLs with invalid dataset IDs fail extraction."""
        with pytest.raises(URLValidationError):
            get_dataset_id_from_url("https://openneuro.org/datasets/invalid")
        
        with pytest.raises(URLValidationError):
            get_dataset_id_from_url("https://openneuro.org/datasets/ds12345")


class TestDatasetIDExtraction:
    """Tests for dataset ID extraction."""
    
    def test_extract_valid_dataset_id(self):
        """Test extraction of valid dataset IDs from URLs."""
        url = "https://openneuro.org/datasets/ds000001"
        assert get_dataset_id_from_url(url) == "ds000001"
        
        url = "https://openneuro.org/datasets/ds000123/files"
        assert get_dataset_id_from_url(url) == "ds000123"
        
        url = "https://openneuro.org/datasets/ds999999/versions/1.0.0"
        assert get_dataset_id_from_url(url) == "ds999999"
    
    def test_extract_dataset_id_with_trailing_slash(self):
        """Test extraction with trailing slash in URL."""
        url = "https://openneuro.org/datasets/ds000001/"
        assert get_dataset_id_from_url(url) == "ds000001"


class TestChecksumFunctions:
    """Tests for checksum computation and verification."""
    
    def test_compute_checksum(self):
        """Test checksum computation on a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)
    
    def test_compute_checksum_different_content(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("content1")
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("content2")
            path2 = f2.name
        
        try:
            checksum1 = compute_file_checksum(path1)
            checksum2 = compute_file_checksum(path2)
            assert checksum1 != checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)
    
    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_file_checksum(temp_path)
            assert verify_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)
    
    def test_verify_checksum_failure(self):
        """Test failed checksum verification raises error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            with pytest.raises(ChecksumError):
                verify_checksum(temp_path, "wrongchecksum")
        finally:
            os.unlink(temp_path)
    
    def test_verify_checksum_file_not_found(self):
        """Test verification of non-existent file raises error."""
        with pytest.raises(ChecksumError):
            verify_checksum("/nonexistent/file.txt", "checksum")


class TestDownloadDataset:
    """Tests for dataset download functionality."""
    
    @patch('src.datasets.download_datasets.OpenNeuroClient')
    def test_download_dataset_invalid_id(self, mock_client):
        """Test that invalid dataset ID format raises error."""
        with pytest.raises(URLValidationError):
            download_dataset("invalid")
    
    @patch('src.datasets.download_datasets.OpenNeuroClient')
    def test_download_dataset_not_found(self, mock_client):
        """Test handling of dataset not found."""
        mock_client.return_value.get_dataset_info.side_effect = Exception("Dataset not found")
        
        with pytest.raises(DownloadError):
            download_dataset("ds000001")
    
    @patch('src.datasets.download_datasets.download_file')
    @patch('src.datasets.download_datasets.OpenNeuroClient')
    def test_download_dataset_success(self, mock_client, mock_download):
        """Test successful dataset download."""
        mock_client.return_value.get_dataset_info.return_value = {
            'files': [
                {'url': 'https://example.com/file1.nii', 'filename': 'file1.nii'},
                {'url': 'https://example.com/file2.nii', 'filename': 'file2.nii'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_dataset("ds000001", tmpdir)
            
            assert result['dataset_id'] == "ds000001"
            assert result['status'] == "success"
            assert len(result['files']) == 2


class TestDownloadDatasetsFromList:
    """Tests for batch dataset download."""
    
    @patch('src.datasets.download_datasets.download_dataset')
    def test_download_datasets_from_list_success(self, mock_download):
        """Test successful batch download."""
        mock_download.return_value = {
            'dataset_id': 'ds000001',
            'status': 'success'
        }
        
        result = download_datasets_from_list(['ds000001', 'ds000002'])
        
        assert result['total'] == 2
        assert result['successful'] == 2
        assert result['failed'] == 0
    
    @patch('src.datasets.download_datasets.download_dataset')
    def test_download_datasets_from_list_partial_failure(self, mock_download):
        """Test batch download with some failures."""
        mock_download.side_effect = [
            {'dataset_id': 'ds000001', 'status': 'success'},
            DownloadError("Failed to download"),
            {'dataset_id': 'ds000003', 'status': 'success'}
        ]
        
        result = download_datasets_from_list(['ds000001', 'ds000002', 'ds000003'])
        
        assert result['total'] == 3
        assert result['successful'] == 2
        assert result['failed'] == 1