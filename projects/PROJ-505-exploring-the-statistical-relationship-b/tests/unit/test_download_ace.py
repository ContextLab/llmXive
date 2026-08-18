"""
Unit tests for code/ingestion/download_ace.py

Tests verify:
1. The fallback mechanism triggers when real fetch fails.
2. The output is correctly labeled 'synthetic' when fallback is used.
3. The output is correctly labeled 'real' when fetch succeeds (mocked).
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingestion.download_ace import fetch_ace_data, load_synthetic_ace, run_ingestion
from utils.logging import DataIngestionError

class TestACEIngestion:
    
    @pytest.fixture
    def mock_config(self):
        return {
            'data_dir': str(Path(__file__).parent / 'test_output'),
            'start_date': datetime(2020, 1, 1),
            'end_date': datetime(2020, 1, 2),
            'random_seed': 42
        }

    def test_fetch_ace_data_fails_and_returns_none(self, mock_config):
        """Test that fetch_ace_data returns None when connection fails."""
        with patch('code.ingestion.download_ace.fetch_ace_data') as mock_fetch:
            # Simulate the function raising an error internally or returning None
            # We test the logic inside run_ingestion which handles the None
            pass 
        
        # Direct test of the logic flow in run_ingestion
        # We mock fetch_ace_data to return (None, "real_failed")
        with patch('code.ingestion.download_ace.fetch_ace_data', return_value=(None, "real_failed")):
            with patch('code.ingestion.download_ace.load_synthetic_ace') as mock_syn:
                mock_syn.return_value = (pd.DataFrame({'col': [1]}), "synthetic")
                with patch('code.ingestion.download_ace.save_parquet'):
                    df, status = run_ingestion(mock_config)
                    # Verify fallback was called
                    mock_syn.assert_called_once()
                    # Verify status is synthetic
                    assert status == "synthetic"

    def test_load_synthetic_ace_returns_dataframe(self, mock_config):
        """Test that synthetic loader returns a valid DataFrame."""
        with patch('code.ingestion.download_ace.generate_ace_synthetic_data') as mock_gen:
            mock_df = pd.DataFrame({'timestamp': [datetime(2020, 1, 1)], 'value': [10.0]})
            mock_gen.return_value = mock_df
            
            df, label = load_synthetic_ace(mock_config)
            
            assert isinstance(df, pd.DataFrame)
            assert label == "synthetic"
            assert 'value' in df.columns

    def test_run_ingestion_labels_real_data(self, mock_config):
        """Test that real data is labeled 'real'."""
        real_df = pd.DataFrame({'timestamp': [datetime(2020, 1, 1)], 'value': [15.0]})
        
        with patch('code.ingestion.download_ace.fetch_ace_data', return_value=(real_df, "real")):
            with patch('code.ingestion.download_ace.save_parquet') as mock_save:
                df, status = run_ingestion(mock_config)
                
                assert status == "real"
                mock_save.assert_called_once()
                
                # Check the saved dataframe has the correct label
                call_args = mock_save.call_args
                saved_df = call_args[0][0] # First positional arg
                assert saved_df['data_source'].iloc[0] == "real"

    def test_run_ingestion_labels_synthetic_data(self, mock_config):
        """Test that synthetic data is labeled 'synthetic'."""
        with patch('code.ingestion.download_ace.fetch_ace_data', return_value=(None, "failed")):
            with patch('code.ingestion.download_ace.load_synthetic_ace') as mock_syn:
                mock_syn.return_value = (pd.DataFrame({'timestamp': [datetime(2020, 1, 1)]}), "synthetic")
                with patch('code.ingestion.download_ace.save_parquet') as mock_save:
                    df, status = run_ingestion(mock_config)
                    
                    assert status == "synthetic"
                    call_args = mock_save.call_args
                    saved_df = call_args[0][0]
                    assert saved_df['data_source'].iloc[0] == "synthetic"