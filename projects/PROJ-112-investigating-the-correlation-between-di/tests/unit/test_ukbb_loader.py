"""
Unit tests for ukbb_loader module.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import tempfile
import shutil

# Add project root to path if not already
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.ingestion.ukbb_loader import (
    verify_url,
    download_file,
    fetch_ukbb_data,
    calculate_file_checksum,
    EXPECTED_UKBB_META_FILE,
    EXPECTED_UKBB_MICROBIOME_FILE
)

class TestVerifyUrl:
    def test_verify_url_success(self):
        """Test verify_url returns True for a working URL."""
        with patch('src.ingestion.ukbb_loader.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            assert verify_url("http://example.com") is True

    def test_verify_url_failure(self):
        """Test verify_url returns False on timeout."""
        with patch('src.ingestion.ukbb_loader.requests.head') as mock_head:
            mock_head.side_effect = Exception("Timeout")
            assert verify_url("http://broken.com") is False

class TestDownloadFile:
    def test_download_file_success(self, tmp_path):
        """Test successful file download."""
        dest = tmp_path / "test.txt"
        content = b"Hello World"
        
        with patch('src.ingestion.ukbb_loader.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [content]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = download_file("http://example.com/file.txt", dest)
            
            assert result is True
            assert dest.exists()
            assert dest.read_bytes() == content

    def test_download_file_failure(self, tmp_path):
        """Test download fails on request exception."""
        dest = tmp_path / "test.txt"
        
        with patch('src.ingestion.ukbb_loader.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network Error")
            
            result = download_file("http://broken.com/file.txt", dest)
            assert result is False

class TestFetchUkbbData:
    def test_fetch_missing_files_raises_error(self, tmp_path):
        """Test that fetch_ukbb_data raises FileNotFoundError if files are missing."""
        # Ensure files do not exist
        assert not (tmp_path / EXPECTED_UKBB_META_FILE).exists()
        
        with pytest.raises(FileNotFoundError) as excinfo:
            fetch_ukbb_data(tmp_path)
        
        assert "UKBB data files missing" in str(excinfo.value)

    def test_fetch_existing_files_loads_data(self, tmp_path):
        """Test loading data when files exist."""
        meta_file = tmp_path / EXPECTED_UKBB_META_FILE
        micro_file = tmp_path / EXPECTED_UKBB_MICROBIOME_FILE
        
        # Create dummy TSV files
        meta_df = pd.DataFrame({"sample_id": [1, 2], "age": [30, 40]})
        micro_df = pd.DataFrame({"sample": [1, 2], "taxon_A": [10, 20]})
        
        meta_df.to_csv(meta_file, sep='\t', index=False)
        micro_df.to_csv(micro_file, sep='\t', index=False)
        
        loaded_meta, loaded_micro, status = fetch_ukbb_data(tmp_path)
        
        assert status == "loaded_from_disk"
        assert len(loaded_meta) == 2
        assert len(loaded_micro) == 2
        assert "sample_id" in loaded_meta.columns

class TestCalculateFileChecksum:
    def test_checksum_calculation(self, tmp_path):
        """Test checksum is calculated correctly."""
        test_file = tmp_path / "checksum_test.txt"
        content = b"test content for checksum"
        test_file.write_bytes(content)
        
        checksum = calculate_file_checksum(test_file)
        
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)