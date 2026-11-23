"""
Tests for code/download_data.py.
These tests verify that the download logic handles errors correctly
and that the schema validation works as expected.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import fetch_real_data, validate_schema, DataFetchError

class TestValidateSchema:
    def test_valid_schema(self):
        """Test that a dataframe with all required columns passes."""
        df = pd.DataFrame({
            'year': [2010],
            'effect_size': [0.5],
            'sample_size': [100],
            'field': ['Psychology']
        })
        # Should not raise
        validate_schema(df)

    def test_missing_column(self):
        """Test that a dataframe with a missing required column raises DataFetchError."""
        df = pd.DataFrame({
            'year': [2010],
            'effect_size': [0.5],
            # 'sample_size' missing
            'field': ['Psychology']
        })
        with pytest.raises(DataFetchError) as excinfo:
            validate_schema(df)
        assert 'sample_size' in str(excinfo.value)

    def test_empty_dataframe(self):
        """Test that an empty dataframe raises DataFetchError."""
        df = pd.DataFrame(columns=['year', 'effect_size', 'sample_size', 'field'])
        with pytest.raises(DataFetchError) as excinfo:
            validate_schema(df)
        assert 'empty' in str(excinfo.value).lower() or 'Missing columns' in str(excinfo.value)

class TestFetchRealData:
    @patch('download_data.load_dataset')
    def test_fetch_success(self, mock_load_dataset):
        """Test successful fetch and conversion."""
        # Mock the streaming dataset
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = pd.DataFrame({
            'year': [2010],
            'effect_size': [0.5],
            'sample_size': [100],
            'field': ['Psychology']
        })
        mock_load_dataset.return_value = mock_ds

        df = fetch_real_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        mock_load_dataset.assert_called_once()

    @patch('download_data.load_dataset')
    def test_fetch_failure_raises_error(self, mock_load_dataset):
        """Test that network errors raise DataFetchError."""
        mock_load_dataset.side_effect = Exception("Network error")

        with pytest.raises(DataFetchError):
            fetch_real_data()

    @patch('download_data.load_dataset')
    def test_fetch_empty_dataset_raises_error(self, mock_load_dataset):
        """Test that an empty dataset raises DataFetchError."""
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = pd.DataFrame()
        mock_load_dataset.return_value = mock_ds

        with pytest.raises(DataFetchError):
            fetch_real_data()