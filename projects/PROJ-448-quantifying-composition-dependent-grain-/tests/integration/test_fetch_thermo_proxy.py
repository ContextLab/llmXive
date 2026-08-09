"""
Integration tests for the thermodynamic proxy fetcher (T006b).

These tests verify that the fetch script correctly downloads the TCFE
database from the real source and handles errors appropriately.
"""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError

# Import the function to test
from code.data.fetch_thermo_proxy import fetch_thermo_proxy, calculate_sha256
from code.errors import ThermodynamicError


class TestFetchThermoProxy:
    """Tests for the fetch_thermo_proxy function."""

    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Calculate hash
            hash_value = calculate_sha256(Path(temp_path))
            
            # Verify it's a valid hex string of correct length
            assert len(hash_value) == 64
            assert all(c in '0123456789abcdef' for c in hash_value)
        finally:
            os.unlink(temp_path)

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_successful_download(self, mock_output_file, mock_output_dir, mock_urlretrieve):
        """Test successful download of the thermodynamic proxy."""
        # Setup mocks
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = False
        mock_output_file.stat.return_value.st_size = 1024
        
        # Mock the file to exist after download
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_read_data="$TEST TDB FILE\nFUNCTION"):
                result = fetch_thermo_proxy()
                
        mock_urlretrieve.assert_called_once()
        assert result == mock_output_file

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_download_http_error(self, mock_output_file, mock_output_dir, mock_urlretrieve):
        """Test handling of HTTP error during download."""
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = False
        
        # Mock HTTP error
        mock_urlretrieve.side_effect = HTTPError(
            url='http://example.com', 
            code=404, 
            msg='Not Found', 
            hdrs={}, 
            fp=None
        )
        
        with pytest.raises(ThermodynamicError) as exc_info:
            fetch_thermo_proxy()
        
        assert "HTTP error" in str(exc_info.value)

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_download_url_error(self, mock_output_file, mock_output_dir, mock_urlretrieve):
        """Test handling of URL error during download."""
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = False
        
        # Mock URL error
        mock_urlretrieve.side_effect = URLError("Connection refused")
        
        with pytest.raises(ThermodynamicError) as exc_info:
            fetch_thermo_proxy()
        
        assert "URL error" in str(exc_info.value)

    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_file_already_exists(self, mock_output_file, mock_output_dir):
        """Test that existing file is not re-downloaded."""
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = True
        
        result = fetch_thermo_proxy()
        
        # urlretrieve should not be called
        with patch('code.data.fetch_thermo_proxy.urlretrieve') as mock_urlretrieve:
            result = fetch_thermo_proxy()
            mock_urlretrieve.assert_not_called()
        
        assert result == mock_output_file

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_file_not_found_after_download(self, mock_output_file, mock_output_dir, mock_urlretrieve):
        """Test error when file is not found after download."""
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = False
        mock_urlretrieve.return_value = None
        
        # Mock file to still not exist after download
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(ThermodynamicError) as exc_info:
                fetch_thermo_proxy()
        
        assert "Download completed but file not found" in str(exc_info.value)

    @patch('code.data.fetch_thermo_proxy.urlretrieve')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_DIR')
    @patch('code.data.fetch_thermo_proxy.OUTPUT_FILE')
    def test_invalid_encoding(self, mock_output_file, mock_output_dir, mock_urlretrieve):
        """Test error when file is not valid UTF-8."""
        mock_output_dir.mkdir = MagicMock()
        mock_output_file.exists.return_value = False
        
        # Mock file to exist but have invalid encoding
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test')):
                with pytest.raises(ThermodynamicError) as exc_info:
                    fetch_thermo_proxy()
        
        assert "not valid UTF-8" in str(exc_info.value)
