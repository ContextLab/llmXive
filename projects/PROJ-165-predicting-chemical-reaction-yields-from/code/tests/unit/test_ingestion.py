import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.ingestion import ingest_data, fetch_real_data, generate_molspectra_simulation
from src.utils.state_manager import load_state

class TestIngestionLogic:
    
    @patch('src.data.ingestion.requests.get')
    def test_fetch_real_data_success(self, mock_get):
        """Test successful fetch from real source."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"smiles,target_energy\nC,0.5"
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.csv"
            result = fetch_real_data("http://fake.url", dest)
            
            assert result is True
            assert dest.exists()
            mock_get.assert_called_once_with("http://fake.url", timeout=30)

    @patch('src.data.ingestion.requests.get')
    def test_fetch_real_data_404(self, mock_get):
        """Test handling of 404 error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.csv"
            result = fetch_real_data("http://fake.url", dest)
            
            assert result is False
            assert not dest.exists()

    @patch('src.data.ingestion.requests.get')
    def test_fetch_real_data_network_error(self, mock_get):
        """Test that network errors raise exceptions."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "test.csv"
            with pytest.raises(RuntimeError, match="Network error"):
                fetch_real_data("http://fake.url", dest)

    def test_generate_molspectra_simulation(self):
        """Test simulated data generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "simulated.csv"
            generate_molspectra_simulation(dest)
            
            assert dest.exists()
            df = pd.read_csv(dest)
            
            assert len(df) == 5000
            assert "smiles" in df.columns
            assert "target_energy" in df.columns
            assert "spectra_ir" in df.columns
            assert "spectra_raman" in df.columns
            assert "spectra_nmr" in df.columns
            assert "conditions_solvent" in df.columns
            assert "conditions_catalyst" in df.columns
            assert "conditions_temperature" in df.columns

    @patch('src.data.ingestion.fetch_real_data')
    def test_ingest_data_pivot_to_simulation(self, mock_fetch):
        """Test that ingestion pivots to simulation when real source fails."""
        mock_fetch.return_value = False  # Simulate 404
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the RAW_DATA_DIR
            with patch('src.data.ingestion.RAW_DATA_DIR', Path(tmpdir)):
                result = ingest_data(output_filename="test_pivot.csv")
                
                assert result["status"] == "success"
                assert result["source"] == "MolSpectra_Simulated_DFT_Energy"
                assert result["pivot_reason"] is not None
                assert "pivot" in result["pivot_reason"].lower()

    @patch('src.data.ingestion.fetch_real_data')
    def test_ingest_data_success_real_source(self, mock_fetch):
        """Test successful ingestion from real source."""
        mock_fetch.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_file = Path(tmpdir) / "test_real.csv"
            dest_file.write_text("smiles,target_energy\nC,0.5")
            
            with patch('src.data.ingestion.RAW_DATA_DIR', Path(tmpdir)):
                with patch('src.data.ingestion.fetch_real_data', return_value=True):
                    result = ingest_data(output_filename="test_real.csv")
                    
                    assert result["status"] == "success"
                    assert result["source"] == "https://raw.githubusercontent.com/molecular-ml/MolSpectra/main/data/simulated_dft_energy_subset.csv"
                    assert result["pivot_reason"] is None

    def test_ingest_data_network_error_raises(self):
        """Test that network errors in ingestion raise exceptions."""
        import requests
        
        with patch('src.data.ingestion.fetch_real_data') as mock_fetch:
            mock_fetch.side_effect = requests.exceptions.ConnectionError("Network error")
            
            with pytest.raises(RuntimeError, match="Network error"):
                ingest_data()