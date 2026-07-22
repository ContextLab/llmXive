"""
Unit tests for Materials Project data fetcher.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

import sys
# Ensure src is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.ingest.materials_project import (
    get_api_key,
    fetch_materials_data,
    extract_and_normalize,
    save_to_json,
    run_materials_ingestion,
    REQUIRED_FIELDS
)


class TestGetApiKey:
    def test_api_key_present(self, monkeypatch):
        monkeypatch.setenv("MP_API_KEY", "test_key_123")
        assert get_api_key() == "test_key_123"

    def test_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("MP_API_KEY", raising=False)
        assert get_api_key() is None


class TestFetchMaterialsData:
    @patch('src.ingest.materials_project.requests.get')
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "material_id": "mp-123",
                    "pretty_formula": "SiO2",
                    "density": 2.65,
                    "elasticity": {"E_VRH": 70.0}
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_materials_data("fake_key", ["milling"])
        assert len(result) == 1
        assert result[0]["material_id"] == "mp-123"
        mock_get.assert_called_once()

    @patch('src.ingest.materials_project.requests.get')
    def test_connection_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        result = fetch_materials_data("fake_key", ["milling"])
        assert result == []


class TestExtractAndNormalize:
    def test_normalize_fields(self):
        raw = [
            {
                "material_id": "mp-123",
                "pretty_formula": "SiO2",
                "density": 2.65,
                "elasticity": {"E_VRH": 70.0}
            }
        ]
        df = extract_and_normalize(raw)
        
        assert isinstance(df, pd.DataFrame)
        assert "experiment_id" in df.columns
        assert "youngs_modulus" in df.columns
        assert "density" in df.columns
        assert df.loc[0, "experiment_id"] == "mp-123"
        assert df.loc[0, "youngs_modulus"] == 70.0
        assert df.loc[0, "milling_speed"] is None # Not in source

    def test_empty_input(self):
        df = extract_and_normalize([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == REQUIRED_FIELDS


class TestSaveToJson:
    def test_save_creates_file(self):
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            save_to_json(df, path)
            assert path.exists()
            
            with open(path) as f:
                data = json.load(f)
                assert len(data) == 2


class TestRunIngestion:
    @patch('src.ingest.materials_project.get_api_key')
    @patch('src.ingest.materials_project.fetch_materials_data')
    @patch('src.ingest.materials_project.save_to_json')
    def test_run_with_key(self, mock_save, mock_fetch, mock_key):
        mock_key.return_value = "test_key"
        mock_fetch.return_value = [{"material_id": "mp-1", "density": 1.0, "elasticity": {}}]
        
        df = run_materials_ingestion()
        
        assert len(df) == 1
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()

    @patch('src.ingest.materials_project.get_api_key')
    @patch('src.ingest.materials_project.save_to_json')
    def test_run_without_key(self, mock_save, mock_key):
        mock_key.return_value = None
        
        df = run_materials_ingestion()
        
        assert len(df) == 0
        mock_save.assert_called_once()