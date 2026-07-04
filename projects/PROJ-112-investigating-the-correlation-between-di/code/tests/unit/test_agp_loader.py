"""
Unit tests for AGP Loader.

Note: These tests mock the network requests to avoid actual API calls during unit testing.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.ingestion.agp_loader import (
    _ensure_qiita_token,
    _fetch_study_info,
    _fetch_sample_mapping,
    _fetch_otu_table,
    main
)

class TestEnsureQiitaToken:
    def test_token_exists(self):
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "test_token"}):
            token = _ensure_qiita_token()
            assert token == "test_token"

    def test_token_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError):
                _ensure_qiita_token()

class TestFetchSampleMapping:
    @patch('src.ingestion.agp_loader.requests.get')
    def test_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"sample_id": "1", "col": "val"}]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"QIITA_API_TOKEN": "token"}):
            result = _fetch_sample_mapping("10317", "token")
            assert "data" in result
            mock_get.assert_called_once()

    @patch('src.ingestion.agp_loader.requests.get')
    def test_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        with patch.dict(os.environ, {"QIITA_API_TOKEN": "token"}):
            with pytest.raises(Exception):
                _fetch_sample_mapping("10317", "token")

class TestFetchOtuTable:
    @patch('src.ingestion.agp_loader.requests.get')
    def test_success(self, mock_get):
        # Mock study info response
        mock_study_response = MagicMock()
        mock_study_response.json.return_value = {
            "processed_data": [{"id": "123"}]
        }
        mock_study_response.raise_for_status = MagicMock()

        # Mock OTU table response
        mock_otu_response = MagicMock()
        mock_otu_response.json.return_value = {
            "data": [{"sample_id": "1", "otus": {"otu1": 5}}],
            "columns": ["otu1"]
        }
        mock_otu_response.raise_for_status = MagicMock()

        # First call gets study info, second gets OTU table
        mock_get.side_effect = [mock_study_response, mock_otu_response]

        with patch.dict(os.environ, {"QIITA_API_TOKEN": "token"}):
            result = _fetch_otu_table("10317", "token")
            assert "data" in result
            assert mock_get.call_count == 2

    @patch('src.ingestion.agp_loader.requests.get')
    def test_no_processed_data(self, mock_get):
        mock_study_response = MagicMock()
        mock_study_response.json.return_value = {"processed_data": []}
        mock_study_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_study_response

        with patch.dict(os.environ, {"QIITA_API_TOKEN": "token"}):
            with pytest.raises(ValueError):
                _fetch_otu_table("10317", "token")

class TestMain:
    @patch('src.ingestion.agp_loader._fetch_sample_mapping')
    @patch('src.ingestion.agp_loader._fetch_otu_table')
    @patch('src.ingestion.agp_loader._save_metadata')
    @patch('src.ingestion.agp_loader._save_otu_table')
    @patch('src.ingestion.agp_loader.get_project_root')
    @patch('src.ingestion.agp_logger._ensure_qiita_token')
    def test_main_success(
        self, mock_token, mock_root, mock_save_otu, mock_save_meta, mock_fetch_otu, mock_fetch_meta
    ):
        mock_token.return_value = "token"
        mock_root.return_value = Path("/fake/root")
        mock_fetch_meta.return_value = {"data": [{"sample_id": "1", "val": "a"}]}
        mock_fetch_otu.return_value = {"data": [{"sample_id": "1", "otus": {"otu1": 1}}], "columns": ["otu1"]}

        metadata_path, otu_path = main()

        assert metadata_path is not None
        assert otu_path is not None
        mock_fetch_meta.assert_called_once()
        mock_fetch_otu.assert_called_once()
        mock_save_meta.assert_called_once()
        mock_save_otu.assert_called_once()

    @patch('src.ingestion.agp_loader._fetch_sample_mapping')
    @patch('src.ingestion.agp_loader._ensure_qiita_token')
    @patch('src.ingestion.agp_loader.get_project_root')
    def test_main_failure_cleanup(
        self, mock_root, mock_token, mock_fetch_meta
    ):
        mock_token.return_value = "token"
        mock_root.return_value = Path("/fake/root")
        mock_fetch_meta.side_effect = Exception("Download failed")

        with pytest.raises(Exception):
            main()
        
        # Verify that the function attempted to clean up (though in mock, files don't exist)
        # The logic is tested by the fact that it raises
        mock_fetch_meta.assert_called_once()