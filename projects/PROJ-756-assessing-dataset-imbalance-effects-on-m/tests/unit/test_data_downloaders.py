"""
Unit tests for data_downloaders module.

These tests verify the utility functions (checksum, download logic) without
actually hitting the network for every test, except for the integration-style
test which is expected to fail loudly if the network is unreachable or the API changes.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
# Note: We assume the module is in the code/ directory and we are running from project root
import sys
sys.path.insert(0, 'code')

from data_downloaders import calculate_sha256, verify_checksum, download_file

class TestChecksums:
    def test_calculate_sha256_empty_file(self):
        """Test SHA256 calculation on an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            checksum = calculate_sha256(tmp_path)
            # SHA256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            tmp_path.unlink()

    def test_calculate_sha256_known_content(self):
        """Test SHA256 calculation on a file with known content."""
        content = b"Hello, World!"
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            checksum = calculate_sha256(tmp_path)
            # SHA256 of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            tmp_path.unlink()

class TestVerifyChecksum:
    def test_verify_checksum_match(self):
        """Test verification when checksum matches."""
        content = b"Test content"
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            # Calculate actual checksum
            actual = calculate_sha256(tmp_path)
            assert verify_checksum(tmp_path, expected_checksum=actual) is True
        finally:
            tmp_path.unlink()

    def test_verify_checksum_mismatch(self):
        """Test verification when checksum does not match."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test content")
            tmp_path = Path(tmp.name)
        
        try:
            assert verify_checksum(tmp_path, expected_checksum="wrong_checksum") is False
        finally:
            tmp_path.unlink()

    def test_verify_checksum_file_not_found(self):
        """Test verification when file does not exist."""
        non_existent = Path("/tmp/does_not_exist_12345.csv")
        assert verify_checksum(non_existent) is False

class TestDownloadFile:
    def test_download_file_success(self):
        """Test successful download (mocked)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = Path(tmpdir) / "test.csv"
            
            # Mock the requests.get
            with patch('data_downloaders.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response
                
                success, error = download_file("http://example.com/test.csv", dest_path)
                
                assert success is True
                assert error is None
                assert dest_path.exists()
                assert dest_path.read_bytes() == b"chunk1chunk2"

    def test_download_file_failure(self):
        """Test download failure (mocked)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = Path(tmpdir) / "test.csv"
            
            with patch('data_downloaders.requests.get') as mock_get:
                mock_get.side_effect = Exception("Network error")
                
                success, error = download_file("http://example.com/test.csv", dest_path)
                
                assert success is False
                assert error is not None
                assert "Network error" in error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])