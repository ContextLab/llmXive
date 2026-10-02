import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from code.src.ingestion.download_materials_project import (
    fetch_materials_project_entries,
    filter_mgb2_entries,
    save_entries_to_json,
    main
)
from code.src.utils.config import get_materials_project_api_key

class TestGetApiKey:
    def test_api_key_retrieval(self):
        """Test that API key is retrieved from environment."""
        with patch.dict(os.environ, {"MP_API_KEY": "test_key_123"}):
            key = get_materials_project_api_key()
            assert key == "test_key_123"

    def test_missing_api_key(self):
        """Test behavior when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            key = get_materials_project_api_key()
            assert key is None

class TestFilterRelevantEntries:
    def test_filter_mgb2_only(self):
        """Test filtering keeps only MgB2 entries."""
        mock_entries = [
            {
                "material_id": "mp-123",
                "elements": [{"element": "Mg"}, {"element": "B"}],
                "nelements": 2
            },
            {
                "material_id": "mp-456",
                "elements": [{"element": "Mg"}, {"element": "B"}, {"element": "C"}],
                "nelements": 3
            },
            {
                "material_id": "mp-789",
                "elements": [{"element": "Mg"}],
                "nelements": 1
            }
        ]

        filtered = filter_mgb2_entries(mock_entries)

        assert len(filtered) == 1
        assert filtered[0]["material_id"] == "mp-123"

    def test_empty_input(self):
        """Test filtering empty list."""
        filtered = filter_mgb2_entries([])
        assert filtered == []

    def test_no_mgb2_found(self):
        """Test filtering when no MgB2 entries exist."""
        mock_entries = [
            {
                "material_id": "mp-111",
                "elements": [{"element": "Fe"}, {"element": "O"}],
                "nelements": 2
            }
        ]

        filtered = filter_mgb2_entries(mock_entries)
        assert filtered == []

class TestMain:
    @patch('code.src.ingestion.download_materials_project.fetch_materials_project_entries')
    @patch('code.src.ingestion.download_materials_project.filter_mgb2_entries')
    @patch('code.src.ingestion.download_materials_project.save_entries_to_json')
    @patch('code.src.ingestion.download_materials_project.get_materials_project_api_key')
    @patch('code.src.ingestion.download_materials_project.logger')
    def test_main_success(
        self,
        mock_logger,
        mock_get_key,
        mock_save,
        mock_filter,
        mock_fetch
    ):
        """Test successful main execution."""
        mock_get_key.return_value = "valid_key"
        mock_fetch.return_value = [
            {"material_id": "mp-1", "elements": [{"element": "Mg"}, {"element": "B"}], "nelements": 2}
        ]
        mock_filter.return_value = [
            {"material_id": "mp-1", "elements": [{"element": "Mg"}, {"element": "B"}], "nelements": 2}
        ]

        result = main()

        assert result == 0
        mock_save.assert_called_once()

    @patch('code.src.ingestion.download_materials_project.get_materials_project_api_key')
    @patch('code.src.ingestion.download_materials_project.logger')
    def test_main_missing_api_key(self, mock_logger, mock_get_key):
        """Test main fails when API key is missing."""
        mock_get_key.return_value = None

        result = main()

        assert result == 1
        mock_logger.error.assert_called()

    @patch('code.src.ingestion.download_materials_project.fetch_materials_project_entries')
    @patch('code.src.ingestion.download_materials_project.get_materials_project_api_key')
    @patch('code.src.ingestion.download_materials_project.logger')
    def test_main_empty_response(self, mock_logger, mock_get_key, mock_fetch):
        """Test main fails when API returns empty response."""
        mock_get_key.return_value = "valid_key"
        mock_fetch.return_value = []

        result = main()

        assert result == 1
        mock_logger.error.assert_called()

    @patch('code.src.ingestion.download_materials_project.fetch_materials_project_entries')
    @patch('code.src.ingestion.download_materials_project.filter_mgb2_entries')
    @patch('code.src.ingestion.download_materials_project.get_materials_project_api_key')
    @patch('code.src.ingestion.download_materials_project.logger')
    def test_main_empty_filtered(self, mock_logger, mock_get_key, mock_filter, mock_fetch):
        """Test main fails when filtering results in empty list."""
        mock_get_key.return_value = "valid_key"
        mock_fetch.return_value = [{"material_id": "mp-1", "elements": [{"element": "Fe"}], "nelements": 1}]
        mock_filter.return_value = []

        result = main()

        assert result == 1
        mock_logger.error.assert_called()