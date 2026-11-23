"""
Unit tests for the download service.
"""
import pytest
from pathlib import Path
import sys
import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock
from src.services.download import calculate_sha256, verify_download, download_from_huggingface

class TestDownload:
    """Test cases for download functionality."""
    
    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_content = b"test content for hashing"
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            checksum = calculate_sha256(temp_path)
            expected = hashlib.sha256(test_content).hexdigest()
            assert checksum == expected
        finally:
            temp_path.unlink()
    
    def test_verify_download_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_content = b"test content"
            f.write(test_content)
            temp_path = Path(f.name)
        
        try:
            checksum = calculate_sha256(temp_path)
            assert verify_download(temp_path, checksum) is True
        finally:
            temp_path.unlink()
    
    def test_verify_download_mismatch(self):
        """Test checksum verification failure."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Checksum mismatch"):
                verify_download(temp_path, "wrong_checksum")
        finally:
            temp_path.unlink()
    
    def test_verify_download_missing_file(self):
        """Test verification of non-existent file."""
        with pytest.raises(FileNotFoundError):
            verify_download(Path("/nonexistent/file.json"))
    
    @patch('src.services.download.hf_hub_download')
    def test_download_from_huggingface_success(self, mock_hf_download):
        """Test successful HuggingFace download."""
        mock_hf_download.return_value = "/tmp/mock/downloaded.json"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                result = download_from_huggingface(
                    repo_id="test/repo",
                    filename="test.json",
                    output_dir=Path("/tmp/test")
                )
                
                assert result == Path("/tmp/mock/downloaded.json")
                mock_hf_download.assert_called_once()
    
    @patch('src.services.download.hf_hub_download')
    def test_download_from_huggingface_failure(self, mock_hf_download):
        """Test download failure handling."""
        mock_hf_download.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Download failed"):
            download_from_huggingface(
                repo_id="test/repo",
                filename="test.json"
            )