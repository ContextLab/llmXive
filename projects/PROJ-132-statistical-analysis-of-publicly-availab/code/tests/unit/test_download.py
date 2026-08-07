import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests

from src.data.download import (
    get_clo_migratory_list,
    download_and_verify_data,
    compute_sha256,
    ensure_data_available
)


class TestDownloadModule:
    """Unit tests for the download module."""

    def test_compute_sha256_basic(self, tmp_path):
        """Test SHA-256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 hex string length
        assert isinstance(checksum, str)

    @patch('src.data.download.requests.get')
    def test_download_and_verify_data_success(self, mock_get, tmp_path):
        """Test successful data download."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"test data"]
        mock_get.return_value = mock_response
        
        dest = tmp_path / "downloaded.csv"
        result = download_and_verify_data("http://example.com/data.csv", dest)
        
        assert result is True
        assert dest.exists()
        assert dest.read_bytes() == b"test data"

    @patch('src.data.download.requests.get')
    def test_download_and_verify_data_failure(self, mock_get, tmp_path):
        """Test failed data download."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        dest = tmp_path / "downloaded.csv"
        result = download_and_verify_data("http://example.com/data.csv", dest)
        
        assert result is False
        assert not dest.exists()

    @patch('src.data.download.requests.head')
    @patch('src.data.download.requests.get')
    def test_get_clo_migratory_list_cached(self, mock_get, mock_head, tmp_path):
        """Test that cached file is used when available."""
        # Create a fake cached file
        cache_file = Path("data/raw/clo_migratory_list.csv")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal valid CSV
        mock_df = pd.DataFrame({
            'scientificName': ['Test Species'],
            'commonName': ['Test'],
            'order': ['TestOrder'],
            'family': ['TestFamily']
        })
        mock_df.to_csv(cache_file, index=False)
        
        try:
            # Should use cache, not download
            result = get_clo_migratory_list()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert 'scientificName' in result.columns
        finally:
            if cache_file.exists():
                cache_file.unlink()

    @patch('src.data.download.requests.get')
    @patch('src.data.download.requests.head')
    def test_get_clo_migratory_list_download_success(self, mock_head, mock_get, tmp_path):
        """Test successful download when no cache exists."""
        # Mock HEAD requests to succeed
        mock_head_response = MagicMock()
        mock_head_response.status_code = 200
        mock_head.return_value = mock_head_response
        
        # Mock GET request to return valid CSV data
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.iter_content = lambda chunk_size: [b"scientificName,commonName,order,family\nTest,Test,Test,Test"]
        mock_get.return_value = mock_get_response
        
        # Temporarily change cache path for testing
        original_cache = Path("data/raw/clo_migratory_list.csv")
        test_cache = tmp_path / "test_cache.csv"
        
        # Patch the CACHE_PATH in the module
        import src.data.download as download_module
        original_cache_path = download_module.CACHE_PATH
        download_module.CACHE_PATH = test_cache
        
        try:
            result = get_clo_migratory_list()
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert test_cache.exists()
        finally:
            download_module.CACHE_PATH = original_cache_path
            if test_cache.exists():
                test_cache.unlink()

    @patch('src.data.download.requests.get')
    @patch('src.data.download.requests.head')
    def test_get_clo_migratory_list_all_sources_fail(self, mock_head, mock_get):
        """Test that RuntimeError is raised when all sources fail."""
        mock_head.side_effect = requests.RequestException("Network error")
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to retrieve CLO migratory list"):
            get_clo_migratory_list()

    def test_ensure_data_available_success(self, tmp_path):
        """Test ensure_data_available when data exists."""
        # Create a fake cache file
        cache_file = Path("data/raw/clo_migratory_list.csv")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("scientificName,commonName\nTest,Test")
        
        try:
            result = ensure_data_available()
            assert result is True
        finally:
            if cache_file.exists():
                cache_file.unlink()

    def test_ensure_data_available_missing(self, tmp_path):
        """Test ensure_data_available when data is missing and download fails."""
        # Ensure no cache file exists
        cache_file = Path("data/raw/clo_migratory_list.csv")
        if cache_file.exists():
            cache_file.unlink()
        
        with patch('src.data.download.get_clo_migratory_list') as mock_get:
            mock_get.side_effect = RuntimeError("Download failed")
            result = ensure_data_available()
            assert result is False