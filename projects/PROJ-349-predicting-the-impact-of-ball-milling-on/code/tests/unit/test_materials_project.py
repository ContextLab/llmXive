"""
Unit tests for Materials Project Data Fetcher (T012).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.ingest.materials_project import (
    fetch_materials_project_data,
    save_to_json,
    run_materials_project_ingestion
)


@pytest.fixture
def mock_api_response():
    """Mock response from Materials Project API."""
    return {
        "data": [
            {
                "material_id": "mp-12345",
                "formula_pretty": "Fe2O3",
                "density": 5.24,
                "elasticity": {"K_voigt": 150.0},
                "milling_speed": 300,
                "milling_time": 120,
                "ball_to_powder_ratio": 10.0,
                "custom_data": {}
            },
            {
                "material_id": "mp-67890",
                "formula_pretty": "CuO",
                "density": 6.31,
                "elasticity": {"K_voigt": 180.0},
                "milling_speed": 400,
                "milling_time": 180,
                "ball_to_powder_ratio": 15.0,
                "custom_data": {}
            }
        ]
    }


@patch('src.ingest.materials_project.requests.get')
@patch.dict(os.environ, {"MP_API_KEY": "test_key"})
def test_fetch_materials_project_data_success(mock_get, mock_api_response):
    """Test successful data fetching."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_materials_project_data(max_pages=1)

    assert len(data) == 2
    assert data[0]["source_name"] == "Materials Project"
    assert data[0]["source_id"] == "mp-12345"
    assert data[0]["milling_speed"] == 300
    assert data[0]["density"] == 5.24


@patch('src.ingest.materials_project.requests.get')
@patch.dict(os.environ, {"MP_API_KEY": "test_key"})
def test_fetch_materials_project_data_empty(mock_get):
    """Test fetching when API returns empty data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": []}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_materials_project_data(max_pages=1)

    assert len(data) == 0


@patch('src.ingest.materials_project.requests.get')
@patch.dict(os.environ, {"MP_API_KEY": "test_key"})
def test_fetch_materials_project_data_missing_id(mock_get):
    """Test filtering of rows missing source_id."""
    mock_api_response_missing_id = {
        "data": [
            {
                "formula_pretty": "Fe2O3",
                "density": 5.24,
                "elasticity": {"K_voigt": 150.0}
                # missing material_id
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_missing_id
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = fetch_materials_project_data(max_pages=1)

    assert len(data) == 0


@patch.dict(os.environ, {}, clear=True)
def test_fetch_materials_project_data_no_api_key():
    """Test behavior when API key is missing."""
    data = fetch_materials_project_data()
    assert data == []


def test_save_to_json():
    """Test saving data to JSON file."""
    data = [{"source_name": "Test", "source_id": "1", "value": 10}]
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test.json")
        save_to_json(data, filepath)

        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
        assert len(loaded_data) == 1
        assert loaded_data[0]["source_name"] == "Test"


@patch('src.ingest.materials_project.fetch_materials_project_data')
def test_run_materials_project_ingestion(mock_fetch):
    """Test the main ingestion runner."""
    mock_fetch.return_value = [{"source_name": "MP", "source_id": "mp-1"}]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override OUTPUT_FILE in the module
        import src.ingest.materials_project as mp_module
        original_output = mp_module.OUTPUT_FILE
        mp_module.OUTPUT_FILE = os.path.join(tmpdir, "output.json")

        try:
            result = run_materials_project_ingestion()
            assert result is not None
            assert os.path.exists(result)
        finally:
            mp_module.OUTPUT_FILE = original_output