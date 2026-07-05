import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.validation import validate_osm_proxies, fetch_global_soundscapes_data

class TestValidationLogic:
    """Tests for the validation logic of OSM proxies."""

    def test_no_global_soundscapes_justification(self, tmp_path):
        """Test that if Global Soundscapes is unavailable, a justification is logged."""
        # Mock the fetch function to return None
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=None):
            # Create a dummy input file
            input_file = tmp_path / "noise_mapped.csv"
            input_file.write_text("latitude,longitude,noise_level_db\n40.7128,-74.0060,60.0\n")
            
            output_file = tmp_path / "validation_log.csv"
            
            validate_osm_proxies(input_file, output_file)
            
            assert output_file.exists()
            df_log = pd.read_csv(output_file)
            
            # Check that a justification was logged
            assert 'SKIPPED' in df_log['status'].values
            assert any('OSM-only' in str(x) or 'justification' in str(x) for x in df_log['details'])

    def test_validation_with_matches(self, tmp_path):
        """Test validation when Global Soundscapes data is available and matches exist."""
        # Mock Global Soundscapes data
        mock_gs_data = pd.DataFrame({
            'latitude': [40.7128],
            'longitude': [-74.0060],
            'noise_db': [58.0]  # 2 dB difference from OSM (60.0) -> PASS (<=2)
        })
        
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=mock_gs_data):
            input_file = tmp_path / "noise_mapped.csv"
            input_file.write_text("latitude,longitude,noise_level_db\n40.7128,-74.0060,60.0\n")
            
            output_file = tmp_path / "validation_log.csv"
            
            validate_osm_proxies(input_file, output_file)
            
            assert output_file.exists()
            df_log = pd.read_csv(output_file)
            
            # Should have a summary row
            summary_row = df_log[df_log['status'] == 'PASSED']
            assert len(summary_row) > 0
            assert 'Max Deviation: 2.00 dB' in summary_row.iloc[0]['details']

    def test_validation_failure_high_deviation(self, tmp_path):
        """Test validation when deviation exceeds threshold."""
        mock_gs_data = pd.DataFrame({
            'latitude': [40.7128],
            'longitude': [-74.0060],
            'noise_db': [55.0]  # 5 dB difference -> FAIL
        })
        
        with patch('src.analysis.validation.fetch_global_soundscapes_data', return_value=mock_gs_data):
            input_file = tmp_path / "noise_mapped.csv"
            input_file.write_text("latitude,longitude,noise_level_db\n40.7128,-74.0060,60.0\n")
            
            output_file = tmp_path / "validation_log.csv"
            
            validate_osm_proxies(input_file, output_file)
            
            assert output_file.exists()
            df_log = pd.read_csv(output_file)
            
            # Should have a FAILED status
            assert 'FAILED' in df_log['status'].values
            assert any('5.00' in str(x) for x in df_log['details']) # Check for 5.00 deviation

    def test_missing_input_file(self, tmp_path):
        """Test behavior when input file does not exist."""
        input_file = tmp_path / "nonexistent.csv"
        output_file = tmp_path / "validation_log.csv"
        
        validate_osm_proxies(input_file, output_file)
        
        assert output_file.exists()
        df_log = pd.read_csv(output_file)
        assert 'error' in df_log['status'].values
        assert 'Input file not found' in df_log['message'].values

class TestFetchGlobalSoundscapes:
    """Tests for the fetch function."""

    @patch('src.analysis.validation.requests.get')
    def test_successful_fetch(self, mock_get, tmp_path):
        """Test successful fetch and parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "latitude,longitude,noise_db\n40.0,-74.0,50.0\n"
        mock_get.return_value = mock_response
        
        df = fetch_global_soundscapes_data()
        
        assert df is not None
        assert len(df) == 1
        assert 'noise_db' in df.columns

    @patch('src.analysis.validation.requests.get')
    def test_failed_fetch(self, mock_get):
        """Test failed fetch (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        df = fetch_global_soundscapes_data()
        assert df is None

    @patch('src.analysis.validation.requests.get')
    def test_network_error(self, mock_get):
        """Test network exception."""
        mock_get.side_effect = Exception("Network Error")
        
        df = fetch_global_soundscapes_data()
        assert df is None
