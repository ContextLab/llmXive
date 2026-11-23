"""
Unit tests for T001: Dataset Metadata Fetcher.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if running as script
if "code" not in sys.path:
    sys.path.insert(0, "code")

from src.data.ingest import fetch_huggingface_datasets, generate_validation_report

class TestT001DatasetFetcher:
    """Tests for the dataset metadata fetching functionality."""

    @patch('src.data.ingest.requests.get')
    def test_fetch_huggingface_datasets_success(self, mock_get):
        """Test successful fetch of datasets from HuggingFace."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "tactile-eeg-001",
                "name": "Tactile EEG Study",
                "description": "A study on tactile oddball paradigms.",
                "tags": ["task:oddball", "modality:EEG"],
                "downloads": 150
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_huggingface_datasets(["tactile"])

        assert len(result) == 1
        assert result[0]["id"] == "tactile-eeg-001"
        assert result[0]["source"] == "huggingface"
        mock_get.assert_called_once()

    @patch('src.data.ingest.requests.get')
    def test_fetch_huggingface_datasets_no_results(self, mock_get):
        """Test fetch when no datasets are found."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_huggingface_datasets(["nonexistent_keyword"])
        assert len(result) == 0

    def test_generate_validation_report_creates_file(self, tmp_path):
        """Test that the validation report is created correctly."""
        candidates = [
            {
                "id": "test-001",
                "name": "Test Dataset",
                "description": "Test desc",
                "tags": [],
                "downloads": 0,
                "source": "huggingface"
            }
        ]
        output_path = tmp_path / "validation_report.json"
        
        generate_validation_report(candidates, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["candidates_found"] == 1
        assert report["datasets"][0]["id"] == "test-001"
        assert "search_timestamp" in report

    @patch('src.data.ingest.requests.get')
    def test_fetch_handles_request_exception(self, mock_get):
        """Test that network errors are handled gracefully."""
        mock_get.side_effect = Exception("Network error")
        
        result = fetch_huggingface_datasets(["tactile"])
        
        assert result == []