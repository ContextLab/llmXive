import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import json

from src.data.ingestion import (
    fetch_nature_notebook_phenology,
    save_phenology_data,
    run_nature_notebook_ingestion
)
from src.config import get_config

@pytest.fixture
def mock_sites():
    return [
        {"site_id": "site_001", "latitude": 40.7128, "longitude": -74.0060},
        {"site_id": "site_002", "latitude": 34.0522, "longitude": -118.2437}
    ]

@pytest.fixture
def mock_nn_response():
    return {
        "results": [
            {
                "observation_date": "2020-04-15",
                "phenophase_name": "leafing",
                "stage": "1",
                "latitude": 40.71,
                "longitude": -74.00,
                "location_name": "Test Site",
                "site_name": "Test Site Name"
            },
            {
                "observation_date": "2020-04-16",
                "phenophase_name": "flowering",
                "stage": "2",
                "latitude": 34.05,
                "longitude": -118.24,
                "location_name": "Test Site 2",
                "site_name": "Test Site Name 2"
            }
        ]
    }

def test_fetch_nature_notebook_phenology(mock_sites, mock_nn_response):
    with patch('src.data.ingestion.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_nn_response
        mock_get.return_value = mock_response

        df = fetch_nature_notebook_phenology(mock_sites, start_date="2020-01-01", end_date="2020-12-31")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "site_id" in df.columns
        assert "date" in df.columns
        assert "phenophase" in df.columns
        assert df["site_id"].nunique() == 2

def test_fetch_nature_notebook_api_failure(mock_sites):
    with patch('src.data.ingestion.requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch Nature's Notebook data"):
            fetch_nature_notebook_phenology(mock_sites)

def test_fetch_nature_notebook_empty_results(mock_sites):
    with patch('src.data.ingestion.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="No phenology observations found"):
            fetch_nature_notebook_phenology(mock_sites)

def test_save_phenology_data(tmp_path):
    df = pd.DataFrame({
        "site_id": ["s1"],
        "date": pd.to_datetime(["2020-01-01"]),
        "phenophase": ["leafing"]
    })
    output_path = str(tmp_path / "test_phenology.csv")
    
    checksum = save_phenology_data(df, output_path)
    
    assert Path(output_path).exists()
    assert checksum is not None
    assert len(checksum) > 0
    
    # Verify content
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 1

@patch('src.data.ingestion.load_json')
@patch('src.data.ingestion.fetch_nature_notebook_phenology')
@patch('src.data.ingestion.save_phenology_data')
def test_run_nature_notebook_ingestion(mock_save, mock_fetch, mock_load, tmp_path, mock_sites):
    # Mock config to use temp dir
    mock_config = {
        "paths": {
            "selected_sites": str(tmp_path / "sites.json"),
            "phenology_observations": str(tmp_path / "phenology.csv")
        },
        "data": {
            "start_year": 2020,
            "end_year": 2020,
            "phenology_radius_km": 5.0
        }
    }
    
    # Write mock sites file
    sites_file = Path(mock_config["paths"]["selected_sites"])
    sites_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sites_file, 'w') as f:
        json.dump(mock_sites, f)
    
    mock_load.return_value = mock_sites
    mock_fetch.return_value = pd.DataFrame({
        "site_id": ["s1"],
        "date": pd.to_datetime(["2020-01-01"]),
        "phenophase": ["leafing"]
    })
    
    result_path = run_nature_notebook_ingestion()
    
    assert result_path == mock_config["paths"]["phenology_observations"]
    mock_fetch.assert_called_once()
    mock_save.assert_called_once()
