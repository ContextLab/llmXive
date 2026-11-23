import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import pandas as pd

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingest import fetch_real_data, RealDataFetchError

class TestRealDataFetch:
    
    def test_fetch_real_data_no_url_raises_error(self):
        """Test that fetch_real_data raises RealDataFetchError if no URL is configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure no REAL_DATA_URL is set
            if 'REAL_DATA_URL' in os.environ:
                del os.environ['REAL_DATA_URL']
            
            with pytest.raises(RealDataFetchError) as excinfo:
                fetch_real_data()
            
            assert "No verified real data source configured" in str(excinfo.value)

    def test_fetch_real_data_invalid_url_raises_error(self):
        """Test that fetch_real_data raises RealDataFetchError if URL is invalid."""
        invalid_url = "https://invalid-url-that-does-not-exist-12345.com/data.csv"
        with patch.dict(os.environ, {"REAL_DATA_URL": invalid_url}):
            with pytest.raises(RealDataFetchError) as excinfo:
                fetch_real_data()
            assert "Failed to fetch real data" in str(excinfo.value)

    @patch('ingest.pd.read_csv')
    def test_fetch_real_data_success(self, mock_read_csv, tmp_path):
        """Test successful fetch and save."""
        # Mock the dataframe
        mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_read_csv.return_value = mock_df
        
        output_path = str(tmp_path / "test_data.csv")
        
        with patch.dict(os.environ, {"REAL_DATA_URL": "https://example.com/data.csv"}):
            # Patch os.makedirs to avoid issues in temp dir
            with patch('ingest.os.makedirs'):
                result_df = fetch_real_data(output_path)
                
                # Verify read_csv was called
                mock_read_csv.assert_called_once_with("https://example.com/data.csv")
                
                # Verify result
                pd.testing.assert_frame_equal(result_df, mock_df)
                
                # Verify file was saved
                assert os.path.exists(output_path)
                
                # Verify content
                saved_df = pd.read_csv(output_path)
                pd.testing.assert_frame_equal(saved_df, mock_df)

    def test_fetch_real_data_empty_dataset_raises_error(self):
        """Test that fetch_real_data raises error if dataset is empty."""
        mock_df = pd.DataFrame()
        
        with patch('ingest.pd.read_csv', return_value=mock_df):
            with patch.dict(os.environ, {"REAL_DATA_URL": "https://example.com/data.csv"}):
                with patch('ingest.os.makedirs'):
                    with pytest.raises(RealDataFetchError) as excinfo:
                        fetch_real_data()
                    assert "Downloaded dataset is empty" in str(excinfo.value)
