import pytest
import pandas as pd
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
import io

from code.data_ingestion import attempt_il_sapt_download, _generate_synthetics_with_psi4
from code.config import DataIngestionError

class TestAttemptIlsaptDownload:
    """Tests for attempt_il_sapt_download function."""

    def test_download_success(self, tmp_path):
        """Test successful download of IL-SAPT dataset."""
        # Mock response
        mock_data = {
            'cation_id': ['C1', 'C2'],
            'anion_id': ['A1', 'A2'],
            'electrostatic_energy': [-10.0, -12.0],
            'dispersion_energy': [-2.0, -2.5],
            'hbond_energy': [-3.0, -3.5],
            'total_energy': [-15.0, -18.0]
        }
        df = pd.DataFrame(mock_data)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = df.to_json().encode()
        
        with patch('code.data_ingestion.requests.get', return_value=mock_response):
            result = attempt_il_sapt_download('http://example.com/sapt.json')
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert 'cation_id' in result.columns
            assert 'anion_id' in result.columns
            assert 'electrostatic_energy' in result.columns
            assert 'dispersion_energy' in result.columns
            assert 'hbond_energy' in result.columns
            assert 'total_energy' in result.columns

    def test_404_triggers_synthetic(self, tmp_path):
        """Test that 404 error triggers synthetic generation."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        # Create a temporary structures file
        structures_file = tmp_path / "il_structures.json"
        structures_data = [
            {
                'cation_id': 'C1',
                'anion_id': 'A1',
                'cation_smiles': '[Li+]',
                'anion_smiles': '[Cl-]'
            }
        ]
        with open(structures_file, 'w') as f:
            json.dump(structures_data, f)
        
        # Mock the synthetic generation function
        mock_df = pd.DataFrame({
            'cation_id': ['C1'],
            'anion_id': ['A1'],
            'electrostatic_energy': [-10.0],
            'dispersion_energy': [-2.0],
            'hbond_energy': [-3.0],
            'total_energy': [-15.0]
        })
        
        with patch('code.data_ingestion.requests.get', return_value=mock_response):
            with patch('code.data_ingestion._generate_synthetics_with_psi4', return_value=mock_df):
                result = attempt_il_sapt_download('http://example.com/sapt.json')
                
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 1

    def test_non_404_error_raises(self, tmp_path):
        """Test that non-404 HTTP errors raise DataIngestionError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        mock_error = MagicMock()
        mock_error.response = mock_response
        
        with patch('code.data_ingestion.requests.get', side_effect=mock_error):
            with pytest.raises(DataIngestionError):
                attempt_il_sapt_download('http://example.com/sapt.json')

    def test_missing_structures_file_raises(self):
        """Test that missing structures file raises DataIngestionError during synthetic generation."""
        with pytest.raises(DataIngestionError):
            _generate_synthetics_with_psi4('nonexistent.json', 'output.parquet')

class TestGenerateSyntheticsWithPsi4:
    """Tests for _generate_synthetics_with_psi4 function."""

    def test_valid_structures_generation(self, tmp_path):
        """Test synthetic generation with valid structures file."""
        structures_file = tmp_path / "il_structures.json"
        structures_data = [
            {
                'cation_id': 'C1',
                'anion_id': 'A1',
                'cation_smiles': '[Li+]',
                'anion_smiles': '[Cl-]'
            }
        ]
        with open(structures_file, 'w') as f:
            json.dump(structures_data, f)
        
        output_file = tmp_path / "sapt.parquet"
        
        # Mock the helper functions to avoid actual PSI4 calls
        with patch('code.data_ingestion._smiles_to_xyz') as mock_smiles_xyz:
            with patch('code.data_ingestion._combine_xyz') as mock_combine:
                with patch('code.data_ingestion._run_psi4_sapt') as mock_psi4:
                    mock_smiles_xyz.return_value = "1\nTest\n0.0 0.0 0.0\n"
                    mock_combine.return_value = "2\nTest\n0.0 0.0 0.0\n1.0 0.0 0.0\n"
                    mock_psi4.return_value = {
                        'electrostatic': -10.0,
                        'dispersion': -2.0,
                        'hbond': -3.0,
                        'total': -15.0
                    }
                    
                    result = _generate_synthetics_with_psi4(str(structures_file), str(output_file))
                    
                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 1
                    assert result['cation_id'].iloc[0] == 'C1'
                    assert result['anion_id'].iloc[0] == 'A1'
                    
                    # Verify file was created
                    assert output_file.exists()

    def test_invalid_json_raises(self, tmp_path):
        """Test that invalid JSON raises DataIngestionError."""
        structures_file = tmp_path / "il_structures.json"
        with open(structures_file, 'w') as f:
            f.write("invalid json")
        
        with pytest.raises(DataIngestionError):
            _generate_synthetics_with_psi4(str(structures_file), 'output.parquet')

    def test_empty_structures_raises(self, tmp_path):
        """Test that empty structures list raises DataIngestionError."""
        structures_file = tmp_path / "il_structures.json"
        with open(structures_file, 'w') as f:
            json.dump([], f)
        
        with pytest.raises(DataIngestionError):
            _generate_synthetics_with_psi4(str(structures_file), 'output.parquet')
