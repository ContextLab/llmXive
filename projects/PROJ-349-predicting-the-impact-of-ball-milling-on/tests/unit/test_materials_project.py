"""
Unit tests for the Materials Project data fetcher.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

import sys
# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingest.materials_project import (
    get_api_key,
    fetch_milling_entries,
    extract_relevant_fields,
    run_materials_project_ingestion,
    DataIngestionError,
    SourceConnectionError
)


class TestGetApiKey:
    def test_get_api_key_success(self, monkeypatch):
        monkeypatch.setenv("MP_API_KEY", "test_key_123")
        assert get_api_key() == "test_key_123"

    def test_get_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("MP_API_KEY", raising=False)
        with pytest.raises(DataIngestionError) as exc_info:
            get_api_key()
        assert "MP_API_KEY" in str(exc_info.value)


class TestFetchMillingEntries:
    @patch('src.ingest.materials_project.requests.get')
    def test_fetch_success(self, mock_get, monkeypatch):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"material_id": "mp-123", "abstract": "ball milling process", "keywords": ["milling"]}
            ]
        }
        mock_get.return_value = mock_response
        monkeypatch.setenv("MP_API_KEY", "fake_key")

        entries = fetch_milling_entries("fake_key", ["milling"])
        assert len(entries) == 1
        assert entries[0]["material_id"] == "mp-123"

    @patch('src.ingest.materials_project.requests.get')
    def test_fetch_timeout(self, mock_get, monkeypatch):
        mock_get.side_effect = Exception("Timeout")
        monkeypatch.setenv("MP_API_KEY", "fake_key")

        with pytest.raises(SourceConnectionError):
            fetch_milling_entries("fake_key", ["milling"])

    @patch('src.ingest.materials_project.requests.get')
    def test_fetch_empty_results(self, mock_get, monkeypatch):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        monkeypatch.setenv("MP_API_KEY", "fake_key")

        with pytest.raises(DataIngestionError):
            fetch_milling_entries("fake_key", ["milling"])


class TestExtractRelevantFields:
    def test_extract_basic(self):
        entry = {
            "material_id": "mp-456",
            "pretty_formula": "SiO2",
            "properties": {
                "density": 2.65,
                "youngs_modulus": 70.0
            },
            "abstract": "Ball milling of silica.",
            "keywords": ["milling", "silica"]
        }
        record = extract_relevant_fields(entry)

        assert record["experiment_id"] == "mp-456"
        assert record["material_type"] == "SiO2"
        assert record["density"] == 2.65
        assert record["youngs_modulus"] == 70.0
        assert record["raw_text"] == "Ball milling of silica."
        assert record["keywords"] == ["milling", "silica"]
        # Milling params should be None as they aren't in structured fields
        assert record["milling_speed"] is None

    def test_extract_missing_properties(self):
        entry = {
            "material_id": "mp-789",
            "pretty_formula": "Al2O3",
            "properties": {},
            "abstract": "Milling experiment.",
            "keywords": []
        }
        record = extract_relevant_fields(entry)
        assert record["density"] is None
        assert record["youngs_modulus"] is None


class TestRunMaterialIngestion:
    @patch('src.ingest.materials_project.get_api_key')
    @patch('src.ingest.materials_project.fetch_milling_entries')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.ingest.materials_project.Path')
    def test_run_full_flow(self, mock_path_class, mock_open_file, mock_fetch, mock_get_key, tmp_path):
        # Setup mocks
        mock_get_key.return_value = "test_key"
        mock_fetch.return_value = [
            {"material_id": "mp-1", "properties": {"density": 1.0}, "abstract": "milling", "keywords": ["milling"]}
        ]
        
        mock_output_path = MagicMock()
        mock_output_path.parent = tmp_path
        mock_output_path.__truediv__.return_value = tmp_path / "output.json"
        mock_path_class.return_value = mock_output_path
        
        # Run
        result = run_materials_project_ingestion(str(tmp_path / "output.json"))
        
        # Verify
        assert result.exists() or str(result) == str(tmp_path / "output.json")
        mock_open_file.assert_called_once()
        # Check content
        handle = mock_open_file()
        write_calls = [call[0][0] for call in handle.write.call_args_list]
        written_json = "".join(write_calls)
        data = json.loads(written_json)
        assert len(data) == 1
        assert data[0]["experiment_id"] == "mp-1"

    @patch('src.ingest.materials_project.get_api_key')
    @patch('src.ingest.materials_project.fetch_milling_entries')
    def test_run_no_entries(self, mock_fetch, mock_get_key, tmp_path):
        mock_get_key.return_value = "test_key"
        mock_fetch.return_value = []
        
        with pytest.raises(DataIngestionError):
            run_materials_project_ingestion(str(tmp_path / "output.json"))