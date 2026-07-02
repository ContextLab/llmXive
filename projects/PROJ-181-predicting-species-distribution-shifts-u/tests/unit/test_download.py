"""
Unit tests for the download module.
"""

import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from download import fetch_occurrences, add_metadata_columns, TARGET_SPECIES

def test_add_metadata_columns():
    """Test that metadata columns are correctly added."""
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    result = add_metadata_columns(df)

    assert "source_identifier" in result.columns
    assert "download_timestamp" in result.columns
    assert "original_dataset_name" in result.columns

    # Check values
    assert all(result["source_identifier"] == "GBIF")
    assert all(result["original_dataset_name"] == "GBIF Occurrence Download")
    assert len(result["download_timestamp"].unique()) == 1  # All same timestamp

@patch("download.requests.get")
def test_fetch_occurrences_mock(mock_get):
    """Test fetch_occurrences with mocked API response."""
    # Mock response structure
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"decimalLatitude": 40.0, "decimalLongitude": -75.0, "scientificName": "TestSpecies"},
            {"decimalLatitude": 41.0, "decimalLongitude": -76.0, "scientificName": "TestSpecies"}
        ],
        "endOfRecords": True
    }
    mock_get.return_value = mock_response

    records = fetch_occurrences("TestSpecies", 1970, 2000, limit=10)

    assert len(records) == 2
    assert records[0]["decimalLatitude"] == 40.0
    mock_get.assert_called_once()
    params = mock_get.call_args[1]["params"]
    assert params["scientificName"] == "TestSpecies"
    assert params["year"] == "1970,2000"
    assert params["limit"] == 300  # MAX_RESULTS_PER_REQUEST
    assert params["hasCoordinate"] == "true"

def test_target_species_list():
    """Verify that target species list is not empty and contains strings."""
    assert len(TARGET_SPECIES) > 0
    assert all(isinstance(s, str) for s in TARGET_SPECIES)
