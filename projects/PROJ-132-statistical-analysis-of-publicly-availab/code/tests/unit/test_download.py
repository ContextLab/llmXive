import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from src.data.download import get_clo_migratory_list, CACHE_FILE, CACHE_DIR, compute_sha256

from src.data.download import get_clo_migratory_list, check_real_data_available, compute_sha256

class TestDownloadModule:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_dir = CACHE_DIR
        
        # Mock the cache directory
        import src.data.download as download_module
        download_module.CACHE_DIR = Path(self.temp_dir)
        download_module.CACHE_FILE = Path(self.temp_dir) / "clo_migratory_list.csv"
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
        download_module.CACHE_DIR = self.original_cache_dir
        download_module.CACHE_FILE = self.original_cache_dir / "clo_migratory_list.csv"

    def test_compute_sha256_basic(self):
        """Test SHA-256 computation on a simple file."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_sha256(test_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)

    def test_compute_sha256_file_not_found(self):
        """Test SHA-256 computation on a non-existent file."""
        non_existent_file = Path(self.temp_dir) / "non_existent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent_file)

    @patch('src.data.download.requests.get')
    def test_download_success(self, mock_get):
        """Test successful download of CLO migratory list."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"scientific_name,common_name\nTurdus migratorius,American Robin\n"
        mock_get.return_value = mock_response

        df = get_clo_migratory_list(force_download=True)

        assert isinstance(df, pd.DataFrame)
        assert 'scientific_name' in df.columns
        assert len(df) == 1
        assert df.iloc[0]['scientific_name'] == 'Turdus migratorius'
        
        # Verify file was created
        assert CACHE_FILE.exists()

    @patch('src.data.download.requests.get')
    def test_download_failure(self, mock_get):
        """Test handling of download failure."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(RuntimeError):
            get_clo_migratory_list(force_download=True)

    @patch('src.data.download.requests.get')
    def test_download_missing_column(self, mock_get):
        """Test handling of file with missing required columns."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"wrong_column,another_column\nvalue1,value2\n"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError):
            get_clo_migratory_list(force_download=True)

    def test_cache_hit(self):
        """Test that cached file is used when available."""
        # Create a fake cached file
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text("scientific_name,common_name\nTurdus migratorius,Robin\n")

        # Mock requests.get to ensure it's not called
        with patch('src.data.download.requests.get') as mock_get:
            df = get_clo_migratory_list(force_download=False)
            
            mock_get.assert_not_called()
            assert len(df) == 1
            assert df.iloc[0]['scientific_name'] == 'Turdus migratorius'

    @patch('src.data.download.requests.get')
    def test_cache_miss_and_download(self, mock_get):
        """Test download when cache is empty."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"scientific_name,common_name\nTurdus migratorius,Robin\n"
        mock_get.return_value = mock_response

        # Ensure cache file doesn't exist
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()

        df = get_clo_migratory_list(force_download=False)

        mock_get.assert_called_once()
        assert CACHE_FILE.exists()
        assert len(df) == 1