"""
Unit tests for the data ingestion module.
"""

import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path for local testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingestion import _load_real_dft_data, _generate_mol_spectra_data, ingest_data
from src.utils.state_manager import load_state

class TestIngestionLogic:
    def test_load_real_dft_data_success(self):
        """Test that real data loading returns a DataFrame."""
        # Mock the load_dataset to return a known set of data
        mock_item = {"smiles": "CCO", "total_energy": -100.5}
        
        with patch('src.data.ingestion.load_dataset') as mock_load:
            # Simulate streaming iterator
            mock_load.return_value = [mock_item] * 10
            
            df, source = _load_real_dft_data()
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert "total_energy_eV" in df.columns
            assert source == "qm9_hf"

    def test_load_real_dft_data_network_error(self):
        """Test that network errors raise an exception."""
        with patch('src.data.ingestion.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Network timeout")
            
            with pytest.raises(RuntimeError, match="Network error"):
                _load_real_dft_data()

    def test_load_real_dft_data_404_fallback(self):
        """Test that 404 errors trigger the MolSpectra fallback."""
        with patch('src.data.ingestion.load_dataset') as mock_load:
            mock_load.side_effect = Exception("404 Not Found")
            
            with patch('src.data.ingestion._generate_mol_spectra_data') as mock_gen:
                mock_df = pd.DataFrame({"smiles": ["CCO"], "total_energy_eV": [-100.0], "source": ["test"]})
                mock_gen.return_value = (mock_df, "mol_spectra_sim")
                
                df, source = _load_real_dft_data()
                
                assert source == "mol_spectra_sim"
                assert len(df) > 0

    def test_generate_mol_spectra_data_structure(self):
        """Test that simulated data has the correct columns."""
        df, source = _generate_mol_spectra_data()
        
        assert "smiles" in df.columns
        assert "total_energy_eV" in df.columns
        assert "spectrum_ir" in df.columns
        assert source == "mol_spectra_sim"
        assert len(df) > 0

    def test_ingest_data_integration(self):
        """Test the full ingestion flow with mocked dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock paths
            with patch('src.data.ingestion.RAW_DIR', Path(tmpdir)):
                with patch('src.data.ingestion.STATE_DIR', Path(tmpdir) / "state"):
                    with patch('src.data.ingestion._load_real_dft_data') as mock_load:
                        mock_df = pd.DataFrame({"smiles": ["CCO"], "total_energy_eV": [-100.0], "source": ["test"]})
                        mock_load.return_value = (mock_df, "test_source")
                        
                        result_path = ingest_data(seed=42)
                        
                        assert os.path.exists(result_path)
                        assert "test_source" in result_path
                        
                        # Check state update
                        state = load_state()
                        assert "data_ingestion" in state
                        assert state["data_ingestion"]["data_source"] == "test_source"