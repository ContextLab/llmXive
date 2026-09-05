"""
Unit tests for data acquisition module.

These tests verify the acquisition logic using mocked HTTP responses
to ensure error handling paths are covered without requiring network access.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.acquisition import (
    fetch_real_diffusion_data_from_nist,
    fetch_fcc_diffusion_data,
    acquire_and_save_diffusion_data,
    MIN_VALID_ENTRIES,
    MAX_DATA_SIZE_BYTES
)
from config import DATA_DIR


class TestAcquisition:
    """Test cases for data acquisition functions."""

    def test_fetch_data_insufficiency(self):
        """Test that SystemExit is raised when data < 50 entries."""
        # Create mock CSV with only 10 rows
        mock_csv = "col1,col2,col3\n" + "\n".join([f"a{i},b{i},c{i}" for i in range(10)])
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = None
            mock_response.read.return_value = mock_csv.encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            with pytest.raises(SystemExit) as exc_info:
                fetch_real_diffusion_data_from_nist("http://test.com/data.csv")
            
            assert "Data Insufficiency: N < 50" in str(exc_info.value)

    def test_fetch_data_size_exceeded(self):
        """Test that SystemExit is raised when data > 10MB."""
        # Create a mock response that claims to be > 10MB
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = str(MAX_DATA_SIZE_BYTES + 1)
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            with pytest.raises(SystemExit) as exc_info:
                fetch_real_diffusion_data_from_nist("http://test.com/data.csv")
            
            assert "Data Size Exceeded: >10MB constraint violated" in str(exc_info.value)

    def test_fetch_success(self):
        """Test successful fetch of valid data."""
        # Create mock CSV with 100 rows
        mock_csv = "col1,col2,col3\n" + "\n".join([f"a{i},b{i},c{i}" for i in range(100)])
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = None
            mock_response.read.return_value = mock_csv.encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            records = fetch_real_diffusion_data_from_nist("http://test.com/data.csv")
            
            assert len(records) == 100
            assert all(isinstance(r, dict) for r in records)

    def test_fetch_fallback_url(self):
        """Test that fallback URL is attempted on failure."""
        # First call fails, second succeeds
        mock_csv = "col1,col2,col3\n" + "\n".join([f"a{i},b{i},c{i}" for i in range(100)])
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = None
            mock_response.read.return_value = mock_csv.encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            
            # First call raises error, second succeeds
            mock_urlopen.side_effect = [
                Exception("First URL failed"),
                mock_response
            ]
            
            # Should succeed with fallback
            records = fetch_fcc_diffusion_data()
            
            assert len(records) == 100
            assert mock_urlopen.call_count == 2

    def test_acquire_and_save_creates_files(self):
        """Test that acquisition creates expected output files."""
        # Create mock CSV with 100 rows
        mock_csv = "col1,col2,col3\n" + "\n".join([f"a{i},b{i},c{i}" for i in range(100)])
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = None
            mock_response.read.return_value = mock_csv.encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            # Create a temporary directory for testing
            with tempfile.TemporaryDirectory() as tmpdir:
                # Patch the paths
                with patch('code.data.acquisition.DATA_DIR', Path(tmpdir)):
                    with patch('code.data.acquisition.METADATA_PATH', Path(tmpdir) / "raw" / "source_metadata.json"):
                        with patch('code.data.acquisition.OUTPUT_CSV_PATH', Path(tmpdir) / "raw" / "fetched_diffusion.csv"):
                            acquire_and_save_diffusion_data()
                            
                            # Verify files exist
                            csv_path = Path(tmpdir) / "raw" / "fetched_diffusion.csv"
                            meta_path = Path(tmpdir) / "raw" / "source_metadata.json"
                            
                            assert csv_path.exists()
                            assert meta_path.exists()
                            
                            # Verify metadata content
                            with open(meta_path) as f:
                                metadata = json.load(f)
                                assert "source_url" in metadata
                                assert "fetch_timestamp" in metadata