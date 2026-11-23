"""
Unit tests for Materials Project Data Fetcher (Task T012).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.ingest.materials_project import (
    fetch_materials_project_data,
    save_to_json,
    run_materials_project_ingestion,
)
from src.utils.exceptions import DataIngestionError

@pytest.fixture
def mock_api_response():
    return {
        "data": [
            {
                "material_id": "mp-12345",
                "keywords": ["ball milling", "synthesis"],
                "abstract": "Study on ball milling effects.",
                "thermo": {"density": 4.5},
                "structure": {"num_sites": 10},
            },
            {
                "material_id": "mp-67890",
                "keywords": ["milling", "powder"],
                "abstract": "Another milling study.",
                "thermo": {},
                "structure": {"num_sites": 20},
            },
        ]
    }

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_fetch_materials_project_data_success(mock_api_response):
    with patch("src.ingest.materials_project.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Set API key for test
        with patch.dict(os.environ, {"MP_API_KEY": "test-key"}):
            records = fetch_materials_project_data(max_pages=1)

            assert len(records) == 2
            assert records[0]["source_name"] == "Materials Project"
            assert records[0]["source_id"] == "mp-12345"
            assert records[0]["density"] == 4.5
            assert records[1]["source_id"] == "mp-67890"

def test_fetch_materials_project_data_missing_id(mock_api_response):
    # Modify response to include a record without material_id
    mock_api_response["data"].append({"keywords": ["test"]})

    with patch("src.ingest.materials_project.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"MP_API_KEY": "test-key"}):
            records = fetch_materials_project_data(max_pages=1)

            # Should filter out the record without ID
            assert len(records) == 2
            assert all(r["source_id"] is not None for r in records)

def test_fetch_materials_project_data_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        records = fetch_materials_project_data()
        assert records == []

def test_fetch_materials_project_data_empty_response():
    with patch("src.ingest.materials_project.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"MP_API_KEY": "test-key"}):
            records = fetch_materials_project_data(max_pages=1)
            assert records == []

def test_save_to_json(temp_dir):
    data = [{"source_id": "mp-1", "value": 10}]
    output_path = temp_dir / "test.json"

    save_to_json(data, output_path)

    assert output_path.exists()
    with open(output_path, "r") as f:
        loaded = json.load(f)
    assert loaded == data

def test_run_materials_project_ingestion_success(mock_api_response, temp_dir, caplog):
    # Patch the output path to use temp_dir
    with patch("src.ingest.materials_project.OUTPUT_PATH", temp_dir / "output.json"):
        with patch("src.ingest.materials_project.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with patch.dict(os.environ, {"MP_API_KEY": "test-key"}):
                records = run_materials_project_ingestion()

                assert len(records) == 2
                assert (temp_dir / "output.json").exists()

def test_run_materials_project_ingestion_no_data(temp_dir, caplog):
    with patch("src.ingest.materials_project.OUTPUT_PATH", temp_dir / "output.json"):
        with patch("src.ingest.materials_project.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with patch.dict(os.environ, {"MP_API_KEY": "test-key"}):
                records = run_materials_project_ingestion()

                assert records == []
                assert (temp_dir / "output.json").exists()
                with open(temp_dir / "output.json", "r") as f:
                    assert f.read() == "[]"