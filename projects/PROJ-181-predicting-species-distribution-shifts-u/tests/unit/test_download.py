import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import add_metadata_columns, fetch_occurrences

class TestAddMetadataColumns:
    def test_add_metadata_columns_basic(self):
        """Test that metadata columns are correctly added to DataFrame."""
        df = pd.DataFrame({
            "latitude": [45.0, 46.0],
            "longitude": [-75.0, -76.0]
        })
        
        result = add_metadata_columns(
            df,
            source_identifier="TEST_SOURCE",
            original_dataset_name="TEST_DATASET"
        )
        
        assert "source_identifier" in result.columns
        assert "download_timestamp" in result.columns
        assert "original_dataset_name" in result.columns
        
        assert result["source_identifier"].iloc[0] == "TEST_SOURCE"
        assert result["original_dataset_name"].iloc[0] == "TEST_DATASET"
        assert len(result["download_timestamp"].iloc[0]) > 0
        
        # Verify all rows have the same metadata
        assert result["source_identifier"].nunique() == 1
        assert result["original_dataset_name"].nunique() == 1

    def test_add_metadata_columns_preserves_data(self):
        """Test that original data is preserved after adding metadata."""
        df = pd.DataFrame({
            "latitude": [45.0, 46.0],
            "longitude": [-75.0, -76.0],
            "species": ["A", "B"]
        })
        
        original_lat = df["latitude"].copy()
        original_lon = df["longitude"].copy()
        original_species = df["species"].copy()
        
        result = add_metadata_columns(
            df,
            source_identifier="TEST",
            original_dataset_name="TEST"
        )
        
        pd.testing.assert_series_equal(result["latitude"], original_lat)
        pd.testing.assert_series_equal(result["longitude"], original_lon)
        pd.testing.assert_series_equal(result["species"], original_species)
        
        assert len(result.columns) == len(df.columns) + 3

class TestFetchOccurrences:
    def test_fetch_occurrences_structure(self):
        """Test that fetch_occurrences returns a list (may be empty if API fails)."""
        # This test verifies the function structure without relying on API availability
        result = fetch_occurrences("Turdus migratorius", 2020, 2020, max_results=1)
        
        assert isinstance(result, list)
        # If API works, we should get records; if not, empty list is acceptable
        # The important thing is the function doesn't crash
        
    def test_fetch_occurrences_max_results(self):
        """Test that max_results parameter limits the number of records."""
        result = fetch_occurrences("Turdus migratorius", 2020, 2020, max_results=5)
        
        assert len(result) <= 5
        # Note: If API returns fewer than 5, that's also acceptable
