"""
Unit tests for downloaders module.

These tests verify the logic of the downloader functions.
Note: Actual download tests are integration tests and require network access.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import hashlib

# Import the module under test
from code.downloaders import (
    calculate_sha256,
    download_file,
    verify_checksum,
    load_huggingface_dataset,
    download_oqmd_constitution,
    download_aflow_constitution
)

class TestCalculateSHA256:
    def test_calculate_sha256(self):
        """Test SHA-256 calculation on a known string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = f.name
        
        try:
            hash_result = calculate_sha256(temp_path)
            # Known SHA-256 for "test data"
            expected_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            assert hash_result == expected_hash
        finally:
            os.unlink(temp_path)

class TestVerifyChecksum:
    def test_verify_checksum(self):
        """Test checksum verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_path = f.name
        
        try:
            hash_result = calculate_sha256(temp_path)
            assert verify_checksum(temp_path, hash_result) == True
            assert verify_checksum(temp_path, "wrong_hash") == False
        finally:
            os.unlink(temp_path)

class TestLoadHuggingFaceDataset:
    @patch('code.downloaders.load_dataset')
    def test_load_huggingface_success(self, mock_load_dataset):
        """Test successful loading from Hugging Face."""
        # Mock the dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'}
        ]))
        mock_load_dataset.return_value = mock_ds
        
        df = load_huggingface_dataset("test/dataset", split="train")
        
        assert df is not None
        assert len(df) == 3
        assert 'col1' in df.columns
        assert 'col2' in df.columns

    @patch('code.downloaders.load_dataset')
    def test_load_huggingface_failure(self, mock_load_dataset):
        """Test handling of Hugging Face loading failure."""
        mock_load_dataset.side_effect = Exception("Connection error")
        
        result = load_huggingface_dataset("test/dataset", split="train")
        assert result is None

class TestDownloadFile:
    @patch('code.downloaders.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content = MagicMock(return_value=[b'test data'])
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            result = download_file("http://example.com/test.txt", temp_path)
            assert result == True
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('code.downloaders.requests.get')
    def test_download_file_failure(self, mock_get):
        """Test handling of download failure."""
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Network error")
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(RequestException):
                download_file("http://example.com/test.txt", temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestDownloadOQMD:
    @patch('code.downloaders.load_huggingface_dataset')
    @patch('code.downloaders.pd.DataFrame.to_parquet')
    def test_download_oqmd_from_hf(self, mock_to_parquet, mock_load):
        """Test OQMD download from Hugging Face."""
        mock_df = pd.DataFrame({'col1': [1, 2, 3]})
        mock_load.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as f:
            temp_path = f.name
        
        try:
            download_oqmd_constitution(temp_path)
            assert os.path.exists(temp_path)
            mock_load.assert_called_once()
            mock_to_parquet.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('code.downloaders.load_huggingface_dataset')
    @patch('code.downloaders.download_file')
    @patch('code.downloaders.pd.read_csv')
    def test_download_oqmd_fallback_to_url(self, mock_read_csv, mock_download, mock_load):
        """Test OQMD download fallback to raw URL."""
        mock_load.return_value = None  # HF failed
        mock_download.return_value = True
        
        # Mock CSV data
        mock_df = pd.DataFrame({'col1': [1, 2, 3]})
        mock_read_csv.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as f:
            temp_path = f.name
        
        try:
            download_oqmd_constitution(temp_path)
            assert os.path.exists(temp_path)
            mock_load.assert_called_once()
            mock_download.assert_called_once()
            mock_read_csv.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestDownloadAFLOW:
    @patch('code.downloaders.load_huggingface_dataset')
    @patch('code.downloaders.pd.DataFrame.to_parquet')
    def test_download_aflow_from_hf(self, mock_to_parquet, mock_load):
        """Test AFLOW download from Hugging Face."""
        mock_df = pd.DataFrame({'col1': [1, 2, 3]})
        mock_load.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as f:
            temp_path = f.name
        
        try:
            download_aflow_constitution(temp_path)
            assert os.path.exists(temp_path)
            mock_load.assert_called_once()
            mock_to_parquet.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('code.downloaders.load_huggingface_dataset')
    @patch('code.downloaders.download_file')
    @patch('code.downloaders.pd.read_csv')
    def test_download_aflow_fallback_to_url(self, mock_read_csv, mock_download, mock_load):
        """Test AFLOW download fallback to raw URL."""
        mock_load.return_value = None  # HF failed
        mock_download.return_value = True
        
        # Mock CSV data
        mock_df = pd.DataFrame({'col1': [1, 2, 3]})
        mock_read_csv.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as f:
            temp_path = f.name
        
        try:
            download_aflow_constitution(temp_path)
            assert os.path.exists(temp_path)
            mock_load.assert_called_once()
            mock_download.assert_called_once()
            mock_read_csv.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)