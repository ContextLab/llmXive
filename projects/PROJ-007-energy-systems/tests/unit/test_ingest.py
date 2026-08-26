"""
Unit tests for data ingestion module.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests

from src.data.ingest import (
    fetch_eia_rec,
    fetch_acs,
    merge_datasets,
    REQUIRED_EIA_COLUMNS,
    REQUIRED_ACS_COLUMNS,
)


class TestFetchEIARec:
    def test_fetch_eia_rec_success(self, tmp_path):
        """Test successful fetch of EIA data."""
        # Mock the response
        mock_csv_content = """income,energy_cost,solar_installation,location,state,county,tract_id
        50000,1200,1,NY,01,001,1001
        30000,1500,0,NY,01,001,1002
        """
        mock_response = MagicMock()
        mock_response.text = mock_csv_content
        mock_response.raise_for_status = MagicMock()

        with patch('src.data.ingest.requests.get', return_value=mock_response):
            df = fetch_eia_rec()

        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 2
        assert set(REQUIRED_EIA_COLUMNS).issubset(df.columns)

    def test_fetch_eia_rec_missing_columns(self, tmp_path):
        """Test failure when required columns are missing."""
        mock_csv_content = """income,energy_cost,location
        50000,1200,NY
        """
        mock_response = MagicMock()
        mock_response.text = mock_csv_content
        mock_response.raise_for_status = MagicMock()

        with patch('src.data.ingest.requests.get', return_value=mock_response):
            with pytest.raises(RuntimeError) as excinfo:
                fetch_eia_rec()

        assert "Missing required columns" in str(excinfo.value)

    def test_fetch_eia_rec_network_error(self, tmp_path):
        """Test failure when network request fails."""
        with patch('src.data.ingest.requests.get', side_effect=requests.exceptions.RequestException("Network error")):
            with pytest.raises(RuntimeError) as excinfo:
                fetch_eia_rec()

        assert "Failed to download EIA RECS data" in str(excinfo.value)


class TestFetchACS:
    def test_fetch_acs_success(self):
        """Test successful fetch of ACS data."""
        # Mock the censusdata download function
        mock_data = MagicMock()
        # Create a mock DataFrame with MultiIndex
        mock_df = pd.DataFrame({
            'B19013_001E': [50000, 60000],
            'B01003_001E': [1000, 2000],
            'B25001_001E': [500, 600],
            'NAME': ['Tract 1001, County A, State X', 'Tract 1002, County B, State Y']
        }, index=pd.MultiIndex.from_tuples([('01', '001', '1001'), ('02', '002', '1002')], names=['state', 'county', 'tract']))
        mock_data.reset_index.return_value = mock_df

        with patch('src.data.ingest.download', return_value=mock_data):
            df = fetch_acs()

        assert isinstance(df, pd.DataFrame)
        assert 'tract_id' in df.columns
        assert set(REQUIRED_ACS_COLUMNS).issubset(df.columns)

    def test_fetch_acs_missing_columns(self):
        """Test failure when ACS data is missing required columns."""
        mock_data = MagicMock()
        mock_df = pd.DataFrame({
            'B19013_001E': [50000],
            'NAME': ['Tract 1001, County A, State X']
        }, index=pd.MultiIndex.from_tuples([('01', '001', '1001')], names=['state', 'county', 'tract']))
        mock_data.reset_index.return_value = mock_df

        with patch('src.data.ingest.download', return_value=mock_data):
            with pytest.raises(RuntimeError) as excinfo:
                fetch_acs()

        assert "Missing required columns" in str(excinfo.value)


class TestMergeDatasets:
    def test_merge_success(self):
        """Test successful merge of EIA and ACS data."""
        eia_df = pd.DataFrame({
            'income': [50000],
            'energy_cost': [1200],
            'solar_installation': [1],
            'location': ['NY'],
            'state': ['01'],
            'county': ['001'],
            'tract_id': ['1001']
        })

        acs_df = pd.DataFrame({
            'tract_id': ['1001'],
            'median_income': [50000],
            'population': [1000],
            'housing_units': [500]
        })

        merged = merge_datasets(eia_df, acs_df)

        assert isinstance(merged, pd.DataFrame)
        assert merged.shape[0] == 1
        assert 'tract_id' in merged.columns

    def test_merge_no_overlap(self):
        """Test failure when no tracts overlap."""
        eia_df = pd.DataFrame({
            'income': [50000],
            'energy_cost': [1200],
            'solar_installation': [1],
            'location': ['NY'],
            'state': ['01'],
            'county': ['001'],
            'tract_id': ['1001']
        })

        acs_df = pd.DataFrame({
            'tract_id': ['2002'],
            'median_income': [60000],
            'population': [2000],
            'housing_units': [600]
        })

        with pytest.raises(RuntimeError) as excinfo:
            merge_datasets(eia_df, acs_df)

        assert "Merge of EIA and ACS datasets resulted in no rows" in str(excinfo.value)
