"""
Unit tests for fail-loud behavior in data ingestion.

Verifies that download_spice and attempt_il_sapt_download raise DataIngestionError
when network failures occur, rather than falling back to synthetic data.
"""
import pytest
import requests
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data_ingestion import download_spice, attempt_il_sapt_download, DataIngestionError


class TestDownloadSpiceFailLoud:
    """Tests for download_spice fail-loud behavior."""
    
    @patch('code.data_ingestion.requests.get')
    def test_network_error_raises_data_ingestion_error(self, mock_get):
        """Test that ConnectionError raises DataIngestionError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network failed")
        
        with pytest.raises(DataIngestionError) as exc_info:
            download_spice("http://example.com/data.parquet")
        
        assert "Network error" in str(exc_info.value)
        assert "Failing loudly" in str(exc_info.value)
    
    @patch('code.data_ingestion.requests.get')
    def test_timeout_raises_data_ingestion_error(self, mock_get):
        """Test that Timeout raises DataIngestionError."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(DataIngestionError) as exc_info:
            download_spice("http://example.com/data.parquet")
        
        assert "Timeout" in str(exc_info.value)
        assert "Failing loudly" in str(exc_info.value)
    
    @patch('code.data_ingestion.requests.get')
    def test_http_error_raises_data_ingestion_error(self, mock_get):
        """Test that HTTP error raises DataIngestionError."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(DataIngestionError) as exc_info:
            download_spice("http://example.com/data.parquet")
        
        assert "Failed to download" in str(exc_info.value)
    
    @patch('code.data_ingestion.requests.get')
    def test_successful_download_returns_dataframe(self, mock_get):
        """Test that successful download returns DataFrame."""
        import pandas as pd
        from io import BytesIO
        
        # Create a minimal valid parquet file in memory
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        parquet_bytes = BytesIO()
        df.to_parquet(parquet_bytes)
        parquet_bytes.seek(0)
        
        mock_response = MagicMock()
        mock_response.content = parquet_bytes.read()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock os.path.exists to return False (no checksum file)
        with patch('code.data_ingestion.os.path.exists', return_value=False):
            result = download_spice("http://example.com/data.parquet")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3


class TestAttemptIlSaptDownloadFailLoud:
    """Tests for attempt_il_sapt_download fail-loud behavior."""
    
    @patch('code.data_ingestion.requests.get')
    def test_connection_error_raises_data_ingestion_error(self, mock_get):
        """Test that ConnectionError raises DataIngestionError without synthetic fallback."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network failed")
        
        with pytest.raises(DataIngestionError) as exc_info:
            attempt_il_sapt_download("http://example.com/sapt.parquet")
        
        assert "Network error" in str(exc_info.value)
        assert "Failing loudly without synthetic fallback" in str(exc_info.value)
    
    @patch('code.data_ingestion.requests.get')
    def test_timeout_raises_data_ingestion_error(self, mock_get):
        """Test that Timeout raises DataIngestionError without synthetic fallback."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(DataIngestionError) as exc_info:
            attempt_il_sapt_download("http://example.com/sapt.parquet")
        
        assert "Timeout" in str(exc_info.value)
        assert "Failing loudly without synthetic fallback" in str(exc_info.value)
    
    @patch('code.data_ingestion.requests.get')
    def test_404_triggers_synthetic_generation(self, mock_get):
        """Test that 404 triggers synthetic generation (not fail-loud)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Mock generate_synthetic_sapt to avoid actual psi4 call
        with patch('code.data_ingestion.generate_synthetic_sapt') as mock_synth:
            import pandas as pd
            mock_synth.return_value = pd.DataFrame({
                'cation_id': ['test'],
                'anion_id': ['test'],
                'electrostatic_energy': [1.0],
                'dispersion_energy': [2.0],
                'hbond_energy': [3.0],
                'total_energy': [6.0]
            })
            
            result = attempt_il_sapt_download("http://example.com/sapt.parquet")
            
        assert isinstance(result, pd.DataFrame)
        mock_synth.assert_called_once()
    
    @patch('code.data_ingestion.requests.get')
    def test_403_triggers_synthetic_generation(self, mock_get):
        """Test that 403 triggers synthetic generation (not fail-loud)."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        with patch('code.data_ingestion.generate_synthetic_sapt') as mock_synth:
            import pandas as pd
            mock_synth.return_value = pd.DataFrame({
                'cation_id': ['test'],
                'anion_id': ['test'],
                'electrostatic_energy': [1.0],
                'dispersion_energy': [2.0],
                'hbond_energy': [3.0],
                'total_energy': [6.0]
            })
            
            result = attempt_il_sapt_download("http://example.com/sapt.parquet")
            
        assert isinstance(result, pd.DataFrame)
        mock_synth.assert_called_once()
    
    @patch('code.data_ingestion.requests.get')
    def test_successful_download_returns_dataframe(self, mock_get):
        """Test that successful download returns DataFrame."""
        import pandas as pd
        from io import BytesIO
        
        df = pd.DataFrame({
            'cation_id': ['test'],
            'anion_id': ['test'],
            'electrostatic_energy': [1.0],
            'dispersion_energy': [2.0],
            'hbond_energy': [3.0],
            'total_energy': [6.0]
        })
        parquet_bytes = BytesIO()
        df.to_parquet(parquet_bytes)
        parquet_bytes.seek(0)
        
        mock_response = MagicMock()
        mock_response.content = parquet_bytes.read()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with patch('code.data_ingestion.os.path.exists', return_value=False):
            result = attempt_il_sapt_download("http://example.com/sapt.parquet")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result['electrostatic_energy'].iloc[0] == 1.0
