import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import requests
from requests.exceptions import Timeout, RequestException

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code import download_data
from code.download_data import (
    get_wesad_download_url, 
    calculate_sha256, 
    download_file_with_checksum, 
    write_checksums, 
    main
)

class TestGetWesadDownloadUrl:
    @patch('code.download_data.requests.get')
    def test_successful_url_extraction(self, mock_get):
        # Mock response data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'files': [
                {'type': 'dataset', 'filename': 'wesad.zip', 'links': {'self': 'https://zenodo.org/api/records/123/files/wesad.zip'}}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        url = get_wesad_download_url()
        assert url == 'https://zenodo.org/api/records/123/files/wesad.zip'
    
    @patch('code.download_data.requests.get')
    def test_no_files_in_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'files': []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="No files found in Zenodo record."):
            get_wesad_download_url()
    
    @patch('code.download_data.requests.get')
    def test_api_request_fails(self, mock_get):
        mock_get.side_effect = RequestException("Network error")
        
        with pytest.raises(RequestException):
            get_wesad_download_url()

class TestCalculateSha256:
    def test_calculate_checksum_valid_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            checksum = calculate_sha256(tmp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            # Known checksum for "test data"
            expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
            assert checksum == expected
        finally:
            os.unlink(tmp_path)
    
    def test_calculate_checksum_nonexistent_file(self):
        with pytest.raises(IOError):
            calculate_sha256("nonexistent_file.txt")

class TestDownloadFileWithChecksum:
    @patch('code.download_data.requests.get')
    def test_successful_download(self, mock_get):
        # Mock a streaming response
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.headers = {'content-length': '16'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.zip")
            checksum = download_file_with_checksum("http://example.com/test.zip", output_path)
            
            assert os.path.exists(output_path)
            assert len(checksum) == 64
    
    @patch('code.download_data.requests.get')
    def test_download_timeout(self, mock_get):
        mock_get.side_effect = Timeout("Download timed out")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.zip")
            # Create a partial file to test deletion
            with open(output_path, 'wb') as f:
                f.write(b"partial")
            
            with pytest.raises(Timeout):
                download_file_with_checksum("http://example.com/test.zip", output_path)
            
            assert not os.path.exists(output_path)
    
    @patch('code.download_data.requests.get')
    def test_download_request_exception(self, mock_get):
        mock_get.side_effect = RequestException("Network error")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.zip")
            with open(output_path, 'wb') as f:
                f.write(b"partial")
            
            with pytest.raises(RequestException):
                download_file_with_checksum("http://example.com/test.zip", output_path)
            
            assert not os.path.exists(output_path)

class TestWriteChecksums:
    def test_write_checksums(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = os.path.join(tmpdir, "checksums.txt")
            write_checksums("abc123", "test.zip", checksum_file)
            
            with open(checksum_file, 'r') as f:
                content = f.read()
            
            assert "abc123" in content
            assert "test.zip" in content

class TestMain:
    @patch('code.download_data.get_wesad_download_url')
    @patch('code.download_data.download_file_with_checksum')
    @patch('code.download_data.write_checksums')
    def test_main_success(self, mock_write, mock_download, mock_get_url):
        mock_get_url.return_value = "http://example.com/wesad.zip"
        mock_download.return_value = "checksum123"
        
        exit_code = main()
        assert exit_code == 0
    
    @patch('code.download_data.get_wesad_download_url')
    def test_main_timeout(self, mock_get_url):
        mock_get_url.side_effect = Timeout("Timeout")
        
        exit_code = main()
        assert exit_code == 1
    
    @patch('code.download_data.get_wesad_download_url')
    def test_main_request_error(self, mock_get_url):
        mock_get_url.side_effect = RequestException("Error")
        
        exit_code = main()
        assert exit_code == 1