"""
Unit tests for T012: USPTO Data Ingestion.
Tests the ingestion logic, checksum verification, and error handling.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import json
import gzip

from src.data.ingestion import (
    compute_file_checksum,
    parse_jsonl_line,
    process_chunk,
    ingest_and_filter,
    stream_jsonl_gz,
    save_provenance
)
from src.utils.logging import get_logger


class TestT012Ingestion:
    """Tests for T012 ingestion logic."""

    def test_compute_file_checksum(self, tmp_path):
        """Test checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

    def test_compute_file_checksum_missing_file(self, tmp_path):
        """Test checksum fails on missing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(tmp_path / "nonexistent.txt")

    def test_parse_jsonl_line_valid(self):
        """Test parsing valid JSONL line."""
        line = '{"id": 1, "name": "test"}'
        result = parse_jsonl_line(line)
        assert result == {"id": 1, "name": "test"}

    def test_parse_jsonl_line_invalid(self):
        """Test parsing invalid JSONL line."""
        line = "not json"
        result = parse_jsonl_line(line)
        assert result is None

    def test_parse_jsonl_line_empty(self):
        """Test parsing empty line."""
        line = ""
        result = parse_jsonl_line(line)
        assert result is None

    def test_process_chunk(self):
        """Test chunk processing into DataFrame."""
        chunk = [{"id": 1}, {"id": 2}]
        df = process_chunk(chunk)
        assert len(df) == 2
        assert "id" in df.columns

    def test_process_chunk_empty(self):
        """Test processing empty chunk."""
        df = process_chunk([])
        assert len(df) == 0

    @patch("src.data.ingestion.urlopen")
    @patch("src.data.ingestion.gzip.open")
    def test_stream_jsonl_gz_success(self, mock_gzip_open, mock_urlopen, tmp_path):
        """Test successful streaming and decompression."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.side_effect = [b"compressed_data", b""]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock gzip file
        mock_gzip_file = MagicMock()
        mock_gzip_file.read.return_value = b'{"id": 1}\n'
        mock_gzip_open.return_value.__enter__.return_value = mock_gzip_file

        output_path = tmp_path / "output.jsonl"
        stream_jsonl_gz("http://example.com/data.jsonl.gz", output_path)

        assert output_path.exists()

    @patch("src.data.ingestion.urlopen")
    def test_stream_jsonl_gz_http_error(self, mock_urlopen, tmp_path):
        """Test handling of HTTP error during download."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", {}, None)

        output_path = tmp_path / "output.jsonl"
        with pytest.raises(ValueError, match="Failed to download"):
            stream_jsonl_gz("http://example.com/data.jsonl.gz", output_path)

    @patch("src.data.ingestion.load_config")
    @patch("src.data.ingestion.stream_jsonl_gz")
    @patch("src.data.ingestion.compute_file_checksum")
    @patch("src.data.ingestion.save_provenance")
    @patch("src.data.ingestion.register_artifact")
    def test_ingest_and_filter_missing_url(self, mock_register, mock_save_prov, mock_checksum, mock_stream, mock_load_config, tmp_path):
        """Test ingestion fails if URL is missing."""
        mock_load_config.return_value = {}
        
        with pytest.raises(ValueError, match="USPTO_URL not configured"):
            ingest_and_filter({})

    @patch("src.data.ingestion.load_config")
    @patch("src.data.ingestion.stream_jsonl_gz")
    @patch("src.data.ingestion.compute_file_checksum")
    @patch("src.data.ingestion.save_provenance")
    @patch("src.data.ingestion.register_artifact")
    @patch("src.data.ingestion.pd.DataFrame")
    def test_ingest_and_filter_success(self, mock_df, mock_register, mock_save_prov, mock_checksum, mock_stream, mock_load_config, tmp_path):
        """Test successful ingestion flow."""
        # Setup mocks
        mock_load_config.return_value = {"USPTO_URL": "http://example.com/data.jsonl.gz"}
        mock_df.return_value = pd.DataFrame([{"id": 1}])
        mock_checksum.return_value = "abc123"
        
        # Run
        result = ingest_and_filter({"USPTO_URL": "http://example.com/data.jsonl.gz"})
        
        assert isinstance(result, pd.DataFrame)
        assert mock_stream.called
        assert mock_register.called
        assert mock_save_prov.called
