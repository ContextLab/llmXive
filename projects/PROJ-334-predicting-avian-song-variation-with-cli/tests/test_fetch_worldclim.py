import os
import sys
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_worldclim import calculate_sha256, update_checksums_file, download_file, fetch_worldclim_data
from config import Config

class TestFetchWorldClim:
    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a temporary file."""
        test_content = b"Hello WorldClim"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(test_content)
        
        checksum = calculate_sha256(str(file_path))
        
        # Verify against known hash
        expected = hashlib.sha256(test_content).hexdigest()
        assert checksum == expected
    
    def test_update_checksums_file(self, tmp_path):
        """Test appending to checksums file."""
        checksum_file = tmp_path / "checksums.txt"
        
        update_checksums_file(str(tmp_path / "data.tif"), "abc123", "test_dataset")
        
        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert "test_dataset" in content
        assert "abc123" in content
    
    @patch('fetch_worldclim.requests.get')
    def test_download_file_success(self, mock_get, tmp_path, caplog):
        """Test successful file download."""
        import logging
        logger = logging.getLogger("test")
        
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content = lambda chunk_size: [b"x" * 50, b"x" * 50]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        output_path = str(tmp_path / "downloaded.tif")
        result = download_file("http://example.com/file.tif", output_path, logger)
        
        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) == 100
    
    @patch('fetch_worldclim.requests.get')
    def test_download_file_failure(self, mock_get, tmp_path, caplog):
        """Test download failure handling."""
        import logging
        logger = logging.getLogger("test")
        
        mock_get.side_effect = Exception("Network Error")
        
        output_path = str(tmp_path / "downloaded.tif")
        result = download_file("http://example.com/file.tif", output_path, logger)
        
        assert result is False
        assert not os.path.exists(output_path)
    
    @patch('fetch_worldclim.download_file')
    def test_fetch_worldclim_data_success(self, mock_download, tmp_path, caplog):
        """Test full fetch workflow."""
        import logging
        logger = logging.getLogger("test")
        
        # Mock config
        mock_config = MagicMock(spec=Config)
        mock_config.data_dir = str(tmp_path)
        
        # Mock download success for all variables
        mock_download.return_value = True
        
        result = fetch_worldclim_data(mock_config, logger)
        
        assert result is True
        assert mock_download.call_count == 3  # bio1, bio12, elev
        assert (tmp_path / "raw").exists()
    
    @patch('fetch_worldclim.download_file')
    def test_fetch_worldclim_data_failure(self, mock_download, tmp_path, caplog):
        """Test fetch abort on first failure."""
        import logging
        logger = logging.getLogger("test")
        
        mock_config = MagicMock(spec=Config)
        mock_config.data_dir = str(tmp_path)
        
        # Fail on first call, succeed on others (shouldn't reach them)
        mock_download.side_effect = [False, True, True]
        
        result = fetch_worldclim_data(mock_config, logger)
        
        assert result is False
        # Should only have called download_file once because of abort logic
        assert mock_download.call_count == 1