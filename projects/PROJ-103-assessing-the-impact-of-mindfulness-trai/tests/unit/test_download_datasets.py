"""
Unit tests for dataset download and validation functions.
"""
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.datasets.download_datasets import (
    validate_url,
    compute_checksum,
    verify_checksum,
    DownloadError,
    ValidationFailedError,
    DOWNLOAD_URL_PATTERN
)


class TestURLValidation:
    """Tests for URL validation functionality."""
    
    def test_valid_url(self):
        """Test that valid OpenNeuro URLs pass validation."""
        valid_urls = [
            "https://openneuro.org/datasets/ds000001/versions/1.0.0",
            "https://openneuro.org/datasets/ds000248/versions/1.2.3",
            "https://openneuro.org/datasets/ds001234/versions/2.0.0"
        ]
        
        for url in valid_urls:
            result = validate_url(url)
            assert result is True
    
    def test_invalid_url_format(self):
        """Test that invalid URLs raise ValidationFailedError."""
        invalid_urls = [
            "https://example.com/datasets/ds000001",
            "http://openneuro.org/datasets/ds000001/versions/1.0.0",
            "https://openneuro.org/datasets/ds000001",
            "https://openneuro.org/datasets/ds000001/versions/invalid",
            "ftp://openneuro.org/datasets/ds000001/versions/1.0.0"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationFailedError):
                validate_url(url)


class TestChecksumFunctions:
    """Tests for checksum computation and verification."""
    
    def test_compute_checksum(self):
        """Test MD5 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data for checksum")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_checksum(tmp_path)
            assert len(checksum) == 32  # MD5 hex digest length
            assert all(c in '0123456789abcdef' for c in checksum.lower())
        finally:
            tmp_path.unlink()
    
    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_checksum(tmp_path)
            result = verify_checksum(tmp_path, checksum)
            assert result is True
        finally:
            tmp_path.unlink()
    
    def test_verify_checksum_failure(self):
        """Test checksum verification failure raises error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            with pytest.raises(ValidationFailedError):
                verify_checksum(tmp_path, "00000000000000000000000000000000")
        finally:
            tmp_path.unlink()


class TestDownloadFunctions:
    """Tests for download functionality (mocked)."""
    
    @patch('src.datasets.download_datasets.requests.get')
    @patch('src.datasets.download_datasets.open', new_callable=mock_open)
    @patch('src.datasets.download_datasets.tqdm')
    def test_download_file_success(self, mock_tqdm, mock_open_func, mock_get):
        """Test successful file download."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test chunk 1', b'test chunk 2']
        mock_response.headers = {'content-length': '20'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = Path(tmpdir) / 'test.txt'
            
            result = download_file('https://example.com/test', dest_path)
            
            assert result == dest_path
            mock_get.assert_called_once()
    
    @patch('src.datasets.download_datasets.requests.get')
    def test_download_file_failure(self, mock_get):
        """Test download failure raises DownloadError."""
        mock_get.side_effect = Exception("Network error")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = Path(tmpdir) / 'test.txt'
            
            with pytest.raises(DownloadError):
                download_file('https://example.com/test', dest_path)
    
    def test_extract_archive_zip(self):
        """Test ZIP archive extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / 'test.zip'
            extract_dir = tmp_path / 'extracted'
            
            # Create a test ZIP file
            import zipfile
            with zipfile.ZipFile(archive_path, 'w') as zf:
                zf.writestr('test.txt', 'test content')
            
            # Extract
            extract_archive(archive_path, extract_dir)
            
            assert extract_dir.exists()
            assert (extract_dir / 'test.txt').exists()
    
    def test_extract_archive_tar_gz(self):
        """Test tar.gz archive extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / 'test.tar.gz'
            extract_dir = tmp_path / 'extracted'
            
            # Create a test tar.gz file
            import tarfile
            with tarfile.open(archive_path, 'w:gz') as tf:
                import io
                data = io.BytesIO(b'test content')
                info = tarfile.TarInfo(name='test.txt')
                info.size = len(b'test content')
                tf.addfile(info, data)
            
            # Extract
            extract_archive(archive_path, extract_dir)
            
            assert extract_dir.exists()
            assert (extract_dir / 'test.txt').exists()


class TestDownloadDatasetIntegration:
    """Integration tests for full dataset download (mocked)."""
    
    @patch('src.datasets.download_datasets.OpenNeuroClient')
    @patch('src.datasets.download_datasets.download_file')
    @patch('src.datasets.download_datasets.extract_archive')
    @patch('src.datasets.download_datasets.compute_checksum')
    def test_download_dataset_success(self, mock_checksum, mock_extract, mock_download, MockClient):
        """Test successful dataset download flow."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.get_dataset_info.return_value = {
            'checksum': 'abc123',
            'name': 'Test Dataset'
        }
        MockClient.return_value = mock_client
        mock_checksum.return_value = 'abc123'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            extract_path, metadata = download_dataset(
                dataset_id='ds000001',
                version='1.0.0',
                output_dir=output_dir,
                verify_checksum=True
            )
            
            assert 'ds000001' in str(extract_path)
            assert metadata['dataset_id'] == 'ds000001'
            mock_client.get_dataset_info.assert_called_once_with('ds000001', '1.0.0')