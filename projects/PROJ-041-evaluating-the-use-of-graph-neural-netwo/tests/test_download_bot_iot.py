import os
import sys
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.download_bot_iot import (
    calculate_sha256,
    download_file,
    validate_file,
    download_bot_iot_dataset,
    trigger_fallback
)

class TestCalculateSha256:
    def test_calculate_sha256(self):
        """Test SHA256 calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        try:
            # Known SHA256 for "test data"
            expected_hash = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
            actual_hash = calculate_sha256(tmp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(tmp_path)

class TestDownloadFile:
    def test_download_file_success(self):
        """Test successful file download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.csv")
            # Mock the download to succeed
            with patch('data.download_bot_iot.urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b"col1,col2\n1,2\n"
                mock_response.__enter__ = lambda self: mock_response
                mock_response.__exit__ = lambda self, *args: None
                mock_urlopen.return_value = mock_response
                
                result = download_file("http://example.com/test.csv", dest_path)
                assert result is True
                assert os.path.exists(dest_path)
                with open(dest_path, 'rb') as f:
                    assert f.read() == b"col1,col2\n1,2\n"

    def test_download_file_failure(self):
        """Test failed file download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.csv")
            with patch('data.download_bot_iot.urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = Exception("Network error")
                
                result = download_file("http://example.com/test.csv", dest_path)
                assert result is False
                assert not os.path.exists(dest_path)

class TestValidateFile:
    def test_validate_file_exists(self):
        """Test validation of existing file."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write("header\nrow\n")
            tmp_path = tmp.name
        
        try:
            assert validate_file(tmp_path) is True
        finally:
            os.unlink(tmp_path)

    def test_validate_file_not_exists(self):
        """Test validation of non-existing file."""
        assert validate_file("/nonexistent/file.csv") is False

    def test_validate_file_empty(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            assert validate_file(tmp_path) is False
        finally:
            os.unlink(tmp_path)

    def test_validate_file_hash_mismatch(self):
        """Test validation with hash mismatch."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write("header\nrow\n")
            tmp_path = tmp.name
        
        try:
            # Provide a wrong hash
            assert validate_file(tmp_path, expected_hash="wronghash") is False
        finally:
            os.unlink(tmp_path)

class TestDownloadBotIotDataset:
    def test_download_bot_iot_dataset_success(self):
        """Test successful download of bot-iot dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the DATA_RAW_DIR
            original_dir = "data/raw"
            # We can't easily change the constant, so we mock the necessary parts
            with patch('data.download_bot_iot.DATA_RAW_DIR', tmpdir):
                with patch('data.download_bot_iot.download_file') as mock_download:
                    mock_download.return_value = True
                    with patch('data.download_bot_iot.validate_file') as mock_validate:
                        mock_validate.return_value = True
                        # Create a dummy file to simulate success
                        dummy_file = os.path.join(tmpdir, "bot-iot_v3.csv")
                        with open(dummy_file, 'w') as f:
                            f.write("col1,col2\n1,2\n")
                        
                        result = download_bot_iot_dataset()
                        assert result == dummy_file
                        assert os.path.exists(result)

    def test_download_bot_iot_dataset_failure(self):
        """Test failure of bot-iot dataset download."""
        with patch('data.download_bot_iot.download_file') as mock_download:
            mock_download.return_value = False
            with pytest.raises(RuntimeError) as excinfo:
                download_bot_iot_dataset()
            assert "Fallback" in str(excinfo.value)

class TestTriggerFallback:
    def test_trigger_fallback_raises_error(self):
        """Test that trigger_fallback raises RuntimeError."""
        with pytest.raises(RuntimeError) as excinfo:
            trigger_fallback()
        assert "Fallback" in str(excinfo.value)