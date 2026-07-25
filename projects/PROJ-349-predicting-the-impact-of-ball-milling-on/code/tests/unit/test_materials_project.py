"""
Unit tests for Materials Project data fetcher (T012)
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.ingest.materials_project import (
    _get_api_key,
    _search_materials,
    _extract_material_data,
    fetch_materials_project_data,
    save_to_json,
    run_materials_project_ingestion
)
from src.exceptions import SourceAuthenticationError, SourceConnectionError, DataIngestionError


class TestMaterialsProjectFetcher:
    """Test cases for Materials Project data fetcher"""

    @patch.dict(os.environ, {"MATERIALS_PROJECT_API_KEY": "test_key_123"})
    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        api_key = _get_api_key()
        assert api_key == "test_key_123"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_missing(self):
        """Test API key retrieval when key is missing"""
        with pytest.raises(SourceAuthenticationError) as exc_info:
            _get_api_key()
        assert "API key not found" in str(exc_info.value)

    @patch('src.ingest.materials_project.requests.get')
    def test_search_materials_success(self, mock_get):
        """Test successful materials search"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "material_id": "mp-123",
                    "pretty_formula": "Fe2O3",
                    "density": 5.24
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = _search_materials("ball milling", page=1, page_size=100)
        assert "data" in result
        assert len(result["data"]) == 1

    @patch('src.ingest.materials_project.requests.get')
    def test_search_materials_connection_error(self, mock_get):
        """Test connection error during search"""
        mock_get.side_effect = Exception("Connection failed")

        with pytest.raises(SourceConnectionError):
            _search_materials("ball milling")

    def test_extract_material_data_basic(self):
        """Test basic data extraction from material entry"""
        raw_material = {
            "material_id": "mp-123",
            "pretty_formula": "Fe2O3",
            "density": 5.24,
            "nelements": 2,
            "nsites": 10,
            "volume": 100.5,
            "space_group": {
                "number": 167,
                "symbol": "R-3c",
                "crystal_system": "trigonal"
            }
        }

        extracted = _extract_material_data(raw_material)

        assert extracted["material_id"] == "mp-123"
        assert extracted["pretty_formula"] == "Fe2O3"
        assert extracted["density"] == 5.24
        assert extracted["source"] == "materials_project"
        assert extracted["milling_speed"] is None  # MP doesn't have this

    def test_extract_material_data_missing_fields(self):
        """Test extraction when some fields are missing"""
        raw_material = {
            "material_id": "mp-456",
            "pretty_formula": "CuO"
        }

        extracted = _extract_material_data(raw_material)

        assert extracted["material_id"] == "mp-456"
        assert extracted["density"] is None
        assert extracted["space_group_number"] is None

    @patch('src.ingest.materials_project._search_materials')
    def test_fetch_materials_project_data_empty_results(self, mock_search):
        """Test fetching when no results are found"""
        mock_search.return_value = {"data": []}

        result = fetch_materials_project_data(max_pages=1)
        assert len(result) == 0

    @patch('src.ingest.materials_project._search_materials')
    def test_fetch_materials_project_data_success(self, mock_search):
        """Test successful data fetching"""
        mock_search.return_value = {
            "data": [
                {"material_id": "mp-1", "pretty_formula": "Fe2O3", "density": 5.24},
                {"material_id": "mp-2", "pretty_formula": "CuO", "density": 6.31}
            ]
        }

        result = fetch_materials_project_data(max_pages=1)
        assert len(result) == 2
        assert result[0]["material_id"] == "mp-1"
        assert result[1]["material_id"] == "mp-2"

    def test_save_to_json_success(self):
        """Test saving data to JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            data = [{"material_id": "mp-1", "density": 5.24}]

            save_to_json(data, output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            assert len(saved_data) == 1
            assert saved_data[0]["material_id"] == "mp-1"

    def test_save_to_json_invalid_path(self):
        """Test saving to invalid path"""
        with pytest.raises(DataIngestionError):
            save_to_json([], Path("/invalid/path/that/does/not/exist/file.json"))

    @patch('src.ingest.materials_project._get_api_key')
    @patch('src.ingest.materials_project.fetch_materials_project_data')
    @patch('src.ingest.materials_project.save_to_json')
    def test_run_materials_project_ingestion_success(
        self, mock_save, mock_fetch, mock_get_key
    ):
        """Test successful ingestion run"""
        mock_get_key.return_value = "test_key"
        mock_fetch.return_value = [{"material_id": "mp-1"}]

        result = run_materials_project_ingestion()

        assert result is True
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()

    @patch('src.ingest.materials_project._get_api_key')
    def test_run_materials_project_ingestion_no_api_key(self, mock_get_key):
        """Test ingestion when API key is missing"""
        mock_get_key.side_effect = SourceAuthenticationError("No key")

        result = run_materials_project_ingestion()

        assert result is False

    @patch('src.ingest.materials_project._get_api_key')
    @patch('src.ingest.materials_project.fetch_materials_project_data')
    def test_run_materials_project_ingestion_no_data(self, mock_fetch, mock_get_key):
        """Test ingestion when no data is returned"""
        mock_get_key.return_value = "test_key"
        mock_fetch.return_value = []

        result = run_materials_project_ingestion()

        assert result is False