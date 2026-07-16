"""
Unit tests for code/data_streamer.py
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data_streamer import download_file_streaming, process_file_batch, stream_data_source

class TestDownloadFileStreaming:
    def test_download_success(self, tmp_path):
        """Test successful download and checksum verification."""
        test_content = b"Hello World"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        dest_path = tmp_path / "test_file.txt"

        with patch('code.data_streamer.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [test_content]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = download_file_streaming("http://example.com/file", dest_path, expected_hash)

            assert result is True
            assert dest_path.exists()
            assert dest_path.read_bytes() == test_content

    def test_download_checksum_mismatch(self, tmp_path):
        """Test that download fails and file is removed on checksum mismatch."""
        test_content = b"Hello World"
        wrong_hash = "0" * 64
        dest_path = tmp_path / "test_file.txt"

        with patch('code.data_streamer.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [test_content]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = download_file_streaming("http://example.com/file", dest_path, wrong_hash)

            assert result is False
            assert not dest_path.exists()

    def test_download_request_exception(self, tmp_path):
        """Test handling of network errors."""
        dest_path = tmp_path / "test_file.txt"

        with patch('code.data_streamer.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network Error")

            result = download_file_streaming("http://example.com/file", dest_path)

            assert result is False
            assert not dest_path.exists()

class TestProcessFileBatch:
    def test_process_batch_success(self, tmp_path):
        """Test processing a batch of files."""
        # Create dummy files
        records = [
            {"url": "http://a.com", "dest_filename": "a.txt", "record_id": "1"},
            {"url": "http://b.com", "dest_filename": "b.txt", "record_id": "2"}
        ]
        
        # Mock the download function to return True immediately
        with patch('code.data_streamer.download_file_streaming') as mock_download:
            mock_download.return_value = True
            
            count = process_file_batch(records, tmp_path)
            
            assert count == 2
            assert mock_download.call_count == 2

    def test_process_batch_partial_failure(self, tmp_path):
        """Test processing a batch where some files fail."""
        records = [
            {"url": "http://a.com", "dest_filename": "a.txt", "record_id": "1"},
            {"url": "http://b.com", "dest_filename": "b.txt", "record_id": "2"}
        ]
        
        with patch('code.data_streamer.download_file_streaming') as mock_download:
            mock_download.side_effect = [True, False]
            
            count = process_file_batch(records, tmp_path)
            
            assert count == 1

class TestStreamDataSource:
    def test_stream_data_source(self, tmp_path):
        """Test the main streaming logic with a manifest."""
        manifest_path = tmp_path / "manifest.json"
        records = [
            {"url": "http://a.com", "dest_filename": "a.txt", "record_id": "1"},
            {"url": "http://b.com", "dest_filename": "b.txt", "record_id": "2"}
        ]
        with open(manifest_path, 'w') as f:
            json.dump(records, f)

        with patch('code.data_streamer.process_file_batch') as mock_process:
            mock_process.return_value = 2
            
            result = stream_data_source(str(manifest_path), tmp_path / "raw")
            
            assert result['total_processed'] == 2
            assert result['failed_count'] == 0

    def test_stream_data_source_missing_manifest(self, tmp_path):
        """Test error handling when manifest is missing."""
        result = stream_data_source(str(tmp_path / "nonexistent.json"), tmp_path)
        assert result['total_processed'] == 0
        assert result['failed_count'] == 0