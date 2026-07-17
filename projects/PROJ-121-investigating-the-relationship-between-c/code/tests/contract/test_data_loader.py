"""
Contract tests for data download integrity.

These tests verify that the data loader correctly:
1. Downloads files from remote sources
2. Verifies SHA-256 checksums
3. Handles network errors appropriately
4. Validates data format after download
"""
import pytest
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
from io import BytesIO

from src.data_loader import (
    calculate_sha256,
    verify_local_checksum,
    download_file,
    DataDownloadError,
    ChecksumVerificationError
)


class TestDataDownloadIntegrity:
    """Contract tests for data download integrity verification."""
    
    def test_calculate_sha256_empty_file(self):
        """Verify SHA-256 calculation for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b'')
        
        try:
            checksum = calculate_sha256(tmp_path)
            # SHA-256 of empty string
            expected = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            assert checksum == expected
        finally:
            os.unlink(tmp_path)
    
    def test_calculate_sha256_known_content(self):
        """Verify SHA-256 calculation for known content."""
        test_content = b"Hello, World!"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(test_content)
        
        try:
            checksum = calculate_sha256(tmp_path)
            assert checksum == expected_hash
        finally:
            os.unlink(tmp_path)
    
    def test_verify_local_checksum_success(self):
        """Verify checksum verification succeeds for matching hash."""
        test_content = b"Test data for checksum verification"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(test_content)
        
        try:
            result = verify_local_checksum(tmp_path, expected_hash)
            assert result is True
        finally:
            os.unlink(tmp_path)
    
    def test_verify_local_checksum_mismatch(self):
        """Verify checksum verification fails for mismatched hash."""
        test_content = b"Test data for checksum verification"
        wrong_hash = "a" * 64  # Invalid hash format
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(test_content)
        
        try:
            with pytest.raises(ChecksumVerificationError):
                verify_local_checksum(tmp_path, wrong_hash)
        finally:
            os.unlink(tmp_path)
    
    def test_download_file_success(self):
        """Verify successful file download with checksum verification."""
        test_content = b"Mock file content for download test"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_content
        mock_response.raise_for_status = MagicMock()
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_file.bin")
                
                result = download_file(
                    url="http://example.com/test.bin",
                    output_path=output_path,
                    expected_checksum=expected_hash
                )
                
                assert result is True
                assert os.path.exists(output_path)
                
                # Verify file content
                with open(output_path, 'rb') as f:
                    assert f.read() == test_content
    
    def test_download_file_checksum_mismatch(self):
        """Verify download fails when checksum doesn't match."""
        test_content = b"Mock file content"
        wrong_hash = "b" * 64
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_content
        mock_response.raise_for_status = MagicMock()
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_file.bin")
                
                with pytest.raises(ChecksumVerificationError):
                    download_file(
                        url="http://example.com/test.bin",
                        output_path=output_path,
                        expected_checksum=wrong_hash
                    )
    
    def test_download_file_network_error(self):
        """Verify download handles network errors appropriately."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.ConnectionError(
            "Network error"
        )
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_file.bin")
                
                with pytest.raises(DataDownloadError):
                    download_file(
                        url="http://example.com/test.bin",
                        output_path=output_path,
                        expected_checksum=None
                    )
    
    def test_download_file_timeout(self):
        """Verify download handles timeout errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.Timeout(
            "Request timed out"
        )
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_file.bin")
                
                with pytest.raises(DataDownloadError):
                    download_file(
                        url="http://example.com/test.bin",
                        output_path=output_path,
                        expected_checksum=None
                    )
    
    def test_file_integrity_preserved_after_download(self):
        """Verify that downloaded file integrity is preserved through checksum."""
        test_content = b"Integrity test content" * 1000
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_content
        mock_response.raise_for_status = MagicMock()
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "integrity_test.bin")
                
                # Download with checksum verification
                success = download_file(
                    url="http://example.com/test.bin",
                    output_path=output_path,
                    expected_checksum=expected_hash
                )
                
                assert success
                
                # Re-calculate checksum to ensure integrity
                recalculated_hash = calculate_sha256(output_path)
                assert recalculated_hash == expected_hash
    
    def test_large_file_download_integrity(self):
        """Verify integrity for larger files (simulated)."""
        # Simulate a larger file (1MB)
        test_content = b"X" * (1024 * 1024)
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = test_content
        mock_response.raise_for_status = MagicMock()
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "large_file.bin")
                
                success = download_file(
                    url="http://example.com/large.bin",
                    output_path=output_path,
                    expected_checksum=expected_hash
                )
                
                assert success
                
                # Verify the file size
                file_size = os.path.getsize(output_path)
                assert file_size == len(test_content)
                
                # Verify checksum
                recalculated_hash = calculate_sha256(output_path)
                assert recalculated_hash == expected_hash
