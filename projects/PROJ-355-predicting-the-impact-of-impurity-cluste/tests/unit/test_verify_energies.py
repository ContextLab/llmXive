"""
Unit tests for verify_energies.py
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config module to avoid dependency on actual project setup
@pytest.fixture
def mock_config():
    with patch('verify_energies.get_project_root') as mock_root, \
         patch('verify_energies.get_data_paths') as mock_paths:
        
        mock_root.return_value = Path('/tmp/test_project')
        mock_paths.return_value = {
            'processed': Path('/tmp/test_project/data/processed')
        }
        yield mock_root, mock_paths

@pytest.fixture
def temp_energies_file(tmp_path, mock_config):
    """Create a temporary energies CSV file for testing."""
    processed_dir = tmp_path / 'data' / 'processed'
    processed_dir.mkdir(parents=True)
    
    file_path = processed_dir / 'segregation_energies.csv'
    
    # Create valid test data
    data = {
        'alloy_system_id': ['BCC_Fe_Cr', 'FCC_Al_Cu', 'BCC_Fe_W'],
        'cluster_metadata': [
            json.dumps({'rdf_peak': 2.5, 'pair_corr': 0.8}),
            json.dumps({'rdf_peak': 2.8, 'pair_corr': 0.9}),
            json.dumps({'rdf_peak': 2.3, 'pair_corr': 0.7})
        ],
        'segregation_energy': [-0.5, -0.3, -0.7]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path

def test_verify_energies_success(temp_energies_file, mock_config):
    """Test successful verification with valid data."""
    from verify_energies import verify_segregation_energies
    
    # Patch the paths to point to our temp file
    with patch('verify_energies.get_data_paths') as mock_paths:
        mock_paths.return_value = {
            'processed': temp_energies_file.parent
        }
        
        result = verify_segregation_energies()
        assert result is True

def test_verify_energies_missing_file(mock_config):
    """Test verification fails when file doesn't exist."""
    from verify_energies import verify_segregation_energies
    
    with patch('verify_energies.get_data_paths') as mock_paths:
        mock_paths.return_value = {
            'processed': Path('/tmp/nonexistent')
        }
        
        result = verify_segregation_energies()
        assert result is False

def test_verify_energies_missing_columns(temp_energies_file, mock_config):
    """Test verification fails when required columns are missing."""
    from verify_energies import verify_segregation_energies
    
    # Create file with missing columns
    data = {
        'alloy_system_id': ['BCC_Fe_Cr'],
        'segregation_energy': [-0.5]
        # Missing cluster_metadata
    }
    df = pd.DataFrame(data)
    df.to_csv(temp_energies_file, index=False)
    
    with patch('verify_energies.get_data_paths') as mock_paths:
        mock_paths.return_value = {
            'processed': temp_energies_file.parent
        }
        
        result = verify_segregation_energies()
        assert result is False

def test_verify_energies_empty_energies(temp_energies_file, mock_config):
    """Test verification fails when energies are all NaN."""
    from verify_energies import verify_segregation_energies
    
    data = {
        'alloy_system_id': ['BCC_Fe_Cr', 'FCC_Al_Cu'],
        'cluster_metadata': ['{}', '{}'],
        'segregation_energy': [None, None]
    }
    df = pd.DataFrame(data)
    df.to_csv(temp_energies_file, index=False)
    
    with patch('verify_energies.get_data_paths') as mock_paths:
        mock_paths.return_value = {
            'processed': temp_energies_file.parent
        }
        
        result = verify_segregation_energies()
        assert result is False