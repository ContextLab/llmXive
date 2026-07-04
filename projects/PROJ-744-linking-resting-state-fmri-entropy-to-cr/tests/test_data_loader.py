"""
Tests for data_loader module.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import hashlib

# Import the module
from code.data_loader import (
    calculate_md5,
    verify_checksum,
    download_from_s3,
    download_hcp_fmri_data,
    download_phenotype_file
)

class TestChecksum:
    """Test checksum calculation and verification."""
    
    def test_calculate_md5(self, tmp_path):
        """Test MD5 calculation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        expected_md5 = hashlib.md5(test_content).hexdigest()
        actual_md5 = calculate_md5(str(test_file))
        
        assert actual_md5 == expected_md5
    
    def test_verify_checksum_success(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)
        
        expected_md5 = hashlib.md5(test_content).hexdigest()
        
        assert verify_checksum(str(test_file), expected_md5) is True
    
    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification with mismatched hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        wrong_md5 = "00000000000000000000000000000000"
        
        assert verify_checksum(str(test_file), wrong_md5) is False
    
    def test_verify_checksum_file_not_found(self):
        """Test checksum verification on non-existent file."""
        assert verify_checksum("/nonexistent/path/file.txt") is False

class TestDownloadFunctions:
    """Test download functions with mocked S3/client."""
    
    @patch('code.data_loader.boto3.client')
    @patch('code.data_loader.tqdm')
    def test_download_from_s3_success(self, mock_tqdm, mock_boto_client, tmp_path):
        """Test successful S3 download."""
        # Setup mocks
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.head_object.return_value = {'ContentLength': 100}
        
        mock_tqdm.return_value.__enter__ = MagicMock()
        mock_tqdm.return_value.__exit__ = MagicMock()
        mock_tqdm.return_value.update = MagicMock()
        
        local_path = tmp_path / "test.nii.gz"
        
        # Mock the download_file to actually create the file
        def mock_download(*args, **kwargs):
            local_path.write_bytes(b"fake nifti data")
            if 'Callback' in kwargs:
                kwargs['Callback'](100)
        
        mock_client_instance.download_file.side_effect = mock_download
        
        # Run test
        result = download_from_s3(
            s3_client=mock_client_instance,
            s3_key="test/key.nii.gz",
            local_path=str(local_path),
            bucket="test-bucket"
        )
        
        assert result is True
        assert local_path.exists()
    
    @patch('code.data_loader.boto3.client')
    @patch('code.data_loader.tqdm')
    def test_download_from_s3_failure(self, mock_tqdm, mock_boto_client, tmp_path):
        """Test failed S3 download."""
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        
        # Simulate download failure
        mock_client_instance.head_object.side_effect = Exception("Access Denied")
        
        local_path = tmp_path / "test.nii.gz"
        
        result = download_from_s3(
            s3_client=mock_client_instance,
            s3_key="test/key.nii.gz",
            local_path=str(local_path),
            bucket="test-bucket"
        )
        
        assert result is False
        assert not local_path.exists()

class TestMainFunctions:
    """Test main download functions."""
    
    @patch('code.data_loader.download_hcp_fmri_data')
    @patch('code.data_loader.download_phenotype_file')
    def test_main_success(self, mock_pheno, mock_fmri):
        """Test main function with successful downloads."""
        mock_fmri.return_value = {
            'status': 'success',
            'downloaded_files': ['data/raw/test.nii.gz'],
            'failed_downloads': [],
            'total_downloaded': 1,
            'total_failed': 0
        }
        mock_pheno.return_value = True
        
        from code.data_loader import main
        
        # This would normally exit with 0
        # We just check that the functions are called correctly
        assert mock_fmri.called
        assert mock_pheno.called
    
    @patch('code.data_loader.download_hcp_fmri_data')
    @patch('code.data_loader.download_phenotype_file')
    def test_main_partial_failure(self, mock_pheno, mock_fmri):
        """Test main function with partial failure."""
        mock_fmri.return_value = {
            'status': 'partial',
            'downloaded_files': [],
            'failed_downloads': [{'subject': '100307', 'reason': 'Not found'}],
            'total_downloaded': 0,
            'total_failed': 1
        }
        mock_pheno.return_value = False
        
        from code.data_loader import main
        
        assert mock_fmri.called
        assert mock_pheno.called