import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_loader import (
    load_m4_hourly_streaming, 
    load_uci_electricity_streaming,
    split_series,
    standardize,
    fetch_data
)
from code.utils.exceptions import DataValidationError, DataFetchError

class TestDataLoader:
    @pytest.fixture
    def mock_csv_data(self):
        """Create mock CSV data for testing."""
        return """ID,V1,V2,V3,V4,V5
        Series1,1.0,2.0,3.0,4.0,5.0
        Series2,10.0,20.0,30.0,40.0,50.0
        Series3,100.0,200.0,300.0,400.0,500.0"""

    @pytest.fixture
    def mock_uci_data(self):
        """Create mock UCI-style data."""
        return """Datetime,Load1,Load2,Load3
        2011-01-01 00:00:00,100.0,200.0,300.0
        2011-01-01 00:15:00,105.0,205.0,305.0
        2011-01-01 00:30:00,110.0,210.0,310.0"""

    def test_split_series_valid(self):
        """Test splitting a valid series."""
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        train, test = split_series(series, train_ratio=0.7)
        
        assert len(train) == 7
        assert len(test) == 3
        assert list(train) == [1, 2, 3, 4, 5, 6, 7]
        assert list(test) == [8, 9, 10]

    def test_split_series_too_short(self):
        """Test splitting a series that is too short."""
        series = pd.Series([1, 2, 3])
        with pytest.raises(DataValidationError):
            split_series(series, train_ratio=0.8)

    def test_standardize_normal(self):
        """Test standardization of a normal series."""
        series = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])
        std_series, mean, std = standardize(series)
        
        assert np.isclose(mean, 6.0)
        assert np.isclose(std, 2.8284271247461903, atol=1e-4)
        assert np.isclose(std_series.mean(), 0.0, atol=1e-6)
        assert np.isclose(std_series.std(), 1.0, atol=1e-6)

    def test_standardize_zero_std(self):
        """Test standardization when std is zero."""
        series = pd.Series([5.0, 5.0, 5.0])
        std_series, mean, std = standardize(series)
        
        assert mean == 5.0
        assert std == 0.0
        # Should return original series when std is zero
        assert list(std_series) == [5.0, 5.0, 5.0]

    @patch('code.data_loader.fetch_data')
    @patch('pandas.read_csv')
    def test_load_m4_streaming_mock(self, mock_read_csv, mock_fetch_data, mock_csv_data):
        """Test M4 streaming loader with mocked data."""
        # Setup mocks
        mock_fetch_data.return_value = Path("/fake/path/m4_hourly.csv")
        mock_df = pd.DataFrame({
            'ID': ['S1', 'S2'],
            'V1': [1.0, 10.0],
            'V2': [2.0, 20.0],
            'V3': [3.0, 30.0]
        })
        mock_read_csv.return_value = mock_df

        # Test streaming
        results = list(load_m4_hourly_streaming(chunk_size=1000))
        
        assert len(results) == 2
        assert results[0]['series_id'] == 'S1'
        assert np.array_equal(results[0]['values'], [1.0, 2.0, 3.0])
        assert results[0]['frequency'] == 'hourly'

    @patch('code.data_loader.fetch_data')
    @patch('pandas.read_csv')
    def test_load_uci_streaming_mock(self, mock_read_csv, mock_fetch_data, mock_uci_data):
        """Test UCI streaming loader with mocked data."""
        # Setup mocks
        mock_fetch_data.return_value = Path("/fake/path/LD2011_2014.txt")
        
        # Mock the sample read for column names
        mock_sample_df = pd.DataFrame({
            'Load1': [100.0, 105.0],
            'Load2': [200.0, 205.0],
            'Load3': [300.0, 305.0]
        }, index=pd.date_range('2011-01-01', periods=2, freq='15min'))
        
        # Mock the chunk read
        mock_chunk_df = pd.DataFrame({
            'Load1': [100.0, 105.0, 110.0],
            'Load2': [200.0, 205.0, 210.0],
            'Load3': [300.0, 305.0, 310.0]
        }, index=pd.date_range('2011-01-01', periods=3, freq='15min'))
        
        # Mock the iterator
        mock_read_csv.side_effect = [mock_sample_df, iter([mock_chunk_df])]

        # Test streaming
        results = list(load_uci_electricity_streaming(chunk_size=1000))
        
        assert len(results) == 3
        assert results[0]['series_id'] == 'Load1'
        assert np.array_equal(results[0]['values'], [100.0, 105.0, 110.0])
        assert results[0]['frequency'] == '15min'

    def test_fetch_data_file_exists(self):
        """Test fetch_data when file already exists."""
        with patch('code.data_loader.DATA_RAW_DIR') as mock_dir:
            mock_dir.__truediv__.return_value.exists.return_value = True
            mock_dir.__truediv__.return_value.__rtruediv__.return_value = Path("/fake/file.csv")
            
            with patch('code.data_logger.logger') as mock_logger:
                result = fetch_data("http://example.com", "file.csv")
                
                mock_logger.info.assert_called()
                # Should not attempt download
                assert result == Path("/fake/file.csv")