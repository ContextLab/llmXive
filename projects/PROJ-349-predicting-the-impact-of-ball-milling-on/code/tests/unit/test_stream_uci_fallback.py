"""
Unit tests for stream_uci_fallback.py (T043).
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from src.exceptions import DataIngestionError
from src.ingest.stream_uci_fallback import (
    load_uci_data,
    map_to_ball_milling_schema,
    stream_and_save_fallback,
    UCI_DATASET_URL,
    FALLBACK_OUTPUT_PATH,
    MIN_ROWS
)

class TestLoadUciData:
    def test_fetch_success(self):
        """Test successful fetch of UCI data."""
        mock_csv = "cycle_number,capacity,voltage,current,temperature,material_type,anode,cathode\n1,100,3.7,1.0,25,Li-ion,Graphite,NMC"
        
        with patch('src.ingest.stream_uci_fallback.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_csv
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            df = load_uci_data()
            
            assert len(df) == 1
            assert 'cycle_number' in df.columns
            mock_get.assert_called_once_with(UCI_DATASET_URL, timeout=30)

    def test_fetch_failure(self):
        """Test fetch failure raises DataIngestionError."""
        with patch('src.ingest.stream_uci_fallback.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            with pytest.raises(DataIngestionError, match="Failed to fetch UCI data"):
                load_uci_data()

    def test_empty_response(self):
        """Test empty response raises DataIngestionError."""
        mock_csv = ""
        
        with patch('src.ingest.stream_uci_fallback.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_csv
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            with pytest.raises(DataIngestionError, match="UCI dataset returned empty DataFrame"):
                load_uci_data()

class TestMapToBallMillingSchema:
    def test_mapping_with_material_type(self):
        """Test mapping when UCI has 'material_type' column."""
        uci_df = pd.DataFrame({
            'material_type': ['Li-ion', 'Lead-acid'],
            'anode': ['Graphite', 'Lead']
        })
        
        mapped_df = map_to_ball_milling_schema(uci_df)
        
        assert len(mapped_df) == 2
        assert 'experiment_id' in mapped_df.columns
        assert 'source' in mapped_df.columns
        assert 'material_type' in mapped_df.columns
        assert mapped_df['material_type'].iloc[0] == 'Li-ion'
        assert mapped_df['source'].iloc[0] == 'UCI_Battery_Fallback'
        
        # Check null columns
        assert mapped_df['milling_speed'].isna().all()
        assert mapped_df['d50'].isna().all()

    def test_mapping_with_anode_only(self):
        """Test mapping when UCI only has 'anode' column."""
        uci_df = pd.DataFrame({
            'anode': ['Graphite', 'Silicon']
        })
        
        mapped_df = map_to_ball_milling_schema(uci_df)
        
        assert len(mapped_df) == 2
        assert mapped_df['material_type'].iloc[0] == 'Graphite'

    def test_mapping_with_no_material_columns(self):
        """Test mapping when UCI has neither 'material_type' nor 'anode'."""
        uci_df = pd.DataFrame({
            'cycle_number': [1, 2]
        })
        
        mapped_df = map_to_ball_milling_schema(uci_df)
        
        assert len(mapped_df) == 2
        assert mapped_df['material_type'].iloc[0] == 'Unknown'

class TestStreamAndSaveFallback:
    @patch('src.ingest.stream_uci_fallback.load_uci_data')
    @patch('src.ingest.stream_uci_fallback.pd.DataFrame.to_csv')
    def test_stream_success(self, mock_to_csv, mock_load):
        """Test successful stream and save."""
        mock_df = pd.DataFrame({
            'experiment_id': ['UCI_0', 'UCI_1'],
            'source': ['UCI_Battery_Fallback', 'UCI_Battery_Fallback'],
            'material_type': ['Li-ion', 'Li-ion']
        })
        mock_load.return_value = mock_df
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override output path for test
            test_path = Path(tmpdir) / "test_fallback.csv"
            with patch.object(__import__('src.ingest.stream_uci_fallback', fromlist=['FALLBACK_OUTPUT_PATH']), 
                              'FALLBACK_OUTPUT_PATH', test_path):
                row_count = stream_and_save_fallback()
                
                assert row_count == 2
                mock_to_csv.assert_called_once()

    @patch('src.ingest.stream_uci_fallback.load_uci_data')
    def test_stream_warning_on_insufficient_rows(self, mock_load):
        """Test warning is logged when rows < MIN_ROWS."""
        mock_df = pd.DataFrame({
            'experiment_id': ['UCI_0'],
            'source': ['UCI_Battery_Fallback'],
            'material_type': ['Li-ion']
        })
        mock_load.return_value = mock_df
        
        with patch('src.ingest.stream_uci_fallback.logger') as mock_logger:
            with tempfile.TemporaryDirectory() as tmpdir:
                test_path = Path(tmpdir) / "test_fallback.csv"
                with patch.object(__import__('src.ingest.stream_uci_fallback', fromlist=['FALLBACK_OUTPUT_PATH']), 
                                  'FALLBACK_OUTPUT_PATH', test_path):
                    row_count = stream_and_save_fallback()
                    
                    assert row_count == 1
                    # Check that warning was logged
                    warning_calls = [call for call in mock_logger.warning.call_args_list 
                                    if "Insufficient real data" in str(call)]
                    assert len(warning_calls) > 0

    @patch('src.ingest.stream_uci_fallback.load_uci_data')
    def test_stream_does_not_halt_on_insufficient_rows(self, mock_load):
        """Test that stream succeeds even if rows < MIN_ROWS."""
        mock_df = pd.DataFrame({
            'experiment_id': ['UCI_0'],
            'source': ['UCI_Battery_Fallback'],
            'material_type': ['Li-ion']
        })
        mock_load.return_value = mock_df
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_fallback.csv"
            with patch.object(__import__('src.ingest.stream_uci_fallback', fromlist=['FALLBACK_OUTPUT_PATH']), 
                              'FALLBACK_OUTPUT_PATH', test_path):
                # Should not raise
                row_count = stream_and_save_fallback()
                assert row_count == 1