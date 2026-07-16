"""
Unit tests for ArXiv PDF Extractor (T014).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.ingest.arxiv_extractor import (
    _hash_bytes,
    _load_flagged_entries,
    _save_flagged_entries,
    _flag_unstructured_entry,
    _parse_psd_from_text,
    extract_psd_from_arxiv
)
from src.exceptions import DataFormatError, SourceConnectionError

class TestHashing:
    def test_hash_bytes(self):
        data = b"test data"
        h = _hash_bytes(data)
        assert len(h) == 64  # SHA-256 hex length
        assert h == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"

class TestFlaggedEntries:
    @pytest.fixture
    def temp_flagged_file(self, tmp_path):
        # Create a temporary file for testing
        flag_file = tmp_path / "flagged_psd.json"
        flag_file.write_text(json.dumps([{"experiment_id": "existing", "source": "test"}]))
        return flag_file

    def test_load_flagged_entries_existing(self, temp_flagged_file):
        # Temporarily override the global path
        import src.ingest.arxiv_extractor as ae
        original_path = ae.FLAGGED_PSD_PATH
        ae.FLAGGED_PSD_PATH = temp_flagged_file
        
        entries = _load_flagged_entries()
        assert len(entries) == 1
        assert entries[0]["experiment_id"] == "existing"
        
        # Restore
        ae.FLAGGED_PSD_PATH = original_path

    def test_load_flagged_entries_missing(self, tmp_path):
        import src.ingest.arxiv_extractor as ae
        original_path = ae.FLAGGED_PSD_PATH
        ae.FLAGGED_PSD_PATH = tmp_path / "nonexistent.json"
        
        entries = _load_flagged_entries()
        assert entries == []
        
        ae.FLAGGED_PSD_PATH = original_path

    def test_flag_unstructured_entry(self, tmp_path):
        import src.ingest.arxiv_extractor as ae
        original_path = ae.FLAGGED_PSD_PATH
        ae.FLAGGED_PSD_PATH = tmp_path / "flagged_psd.json"
        
        _flag_unstructured_entry(
            experiment_id="test_123",
            source="arxiv",
            issue_type="image",
            raw_blob_hash="abc123"
        )
        
        entries = _load_flagged_entries()
        assert len(entries) == 1
        assert entries[0]["experiment_id"] == "test_123"
        
        ae.FLAGGED_PSD_PATH = original_path

class TestTextParsing:
    def test_parse_psd_from_text_found(self):
        text = "The particle size distribution showed a D50 of 15.5 μm."
        result = _parse_psd_from_text(text)
        assert result is not None
        assert "15.5" in result["raw_text_match"]

    def test_parse_psd_from_text_not_found(self):
        text = "This is just random text without any particle size data."
        result = _parse_psd_from_text(text)
        assert result is None

class TestExtractionIntegration:
    @patch('src.ingest.arxiv_extractor._fetch_arxiv_papers')
    @patch('src.ingest.arxiv_extractor._download_pdf')
    @patch('src.ingest.arxiv_extractor._extract_text_from_pdf')
    @patch('src.ingest.arxiv_extractor._detect_images_in_pdf')
    @patch('src.ingest.arxiv_extractor._parse_psd_from_text')
    @patch('src.ingest.arxiv_extractor._flag_unstructured_entry')
    def test_extract_psd_from_arxiv_success(
        self,
        mock_flag,
        mock_parse,
        mock_detect,
        mock_extract_text,
        mock_download,
        mock_fetch,
        tmp_path
    ):
        # Setup mocks
        mock_fetch.return_value = [
            {"arxiv_id": "1234.5678", "title": "Test Paper", "pdf_url": "http://test.com/test.pdf"}
        ]
        mock_download.return_value = tmp_path / "test.pdf"
        mock_extract_text.return_value = "D50: 10 um"
        mock_detect.return_value = [] # No images
        mock_parse.return_value = {"raw_text_match": "10", "source": "text", "confidence": "low"}

        # Run
        records, flagged = extract_psd_from_arxiv(output_dir=tmp_path / "raw", max_papers=1)

        # Assertions
        assert len(records) == 1
        assert records[0]["experiment_id"] == "arxiv_1234.5678"
        assert records[0]["status"] == "processed"
        assert flagged == 0
        mock_flag.assert_not_called()

    @patch('src.ingest.arxiv_extractor._fetch_arxiv_papers')
    @patch('src.ingest.arxiv_extractor._download_pdf')
    @patch('src.ingest.arxiv_extractor._extract_text_from_pdf')
    @patch('src.ingest.arxiv_extractor._detect_images_in_pdf')
    @patch('src.ingest.arxiv_extractor._flag_unstructured_entry')
    def test_extract_psd_from_arxiv_with_images(
        self,
        mock_flag,
        mock_detect,
        mock_extract_text,
        mock_download,
        mock_fetch,
        tmp_path
    ):
        # Setup mocks
        mock_fetch.return_value = [
            {"arxiv_id": "9999.0000", "title": "Image Paper", "pdf_url": "http://test.com/img.pdf"}
        ]
        mock_download.return_value = tmp_path / "img.pdf"
        mock_extract_text.return_value = "No data here"
        mock_detect.return_value = [MagicMock()] # One image detected
        mock_parse.return_value = None

        # Run
        records, flagged = extract_psd_from_arxiv(output_dir=tmp_path / "raw", max_papers=1)

        # Assertions
        assert len(records) == 1
        assert records[0]["status"] == "flagged_unstructured"
        assert flagged == 1
        mock_flag.assert_called_once()
        call_args = mock_flag.call_args
        assert call_args[1]["issue_type"] == "unstructured_psd_image"