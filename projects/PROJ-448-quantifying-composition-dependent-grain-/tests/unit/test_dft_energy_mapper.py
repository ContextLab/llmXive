"""
Unit tests for code/data/dft_energy_mapper.py (Task T049b).

These tests verify the bridge between supercell metadata and DFT energy lookup.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.data.dft_energy_mapper import load_dft_energies, map_supercell_to_dft_energy
from code.errors import DataLoadError
from code.config import DATA_RAW_PATH

@pytest.fixture
def mock_dft_data():
    """Fixture providing sample DFT energy data."""
    return {
        'sigma5_fe_cr': {'system': 'Fe-Cr', 'energy_eV': -0.15, 'temperature': 300},
        'sigma3_fe_mo': {'system': 'Fe-Mo', 'energy_eV': -0.22, 'temperature': 300},
        'sigma5_fe_v': {'system': 'Fe-V', 'energy_eV': -0.18, 'temperature': 300},
    }

@pytest.fixture
def temp_dft_file(mock_dft_data):
    """Fixture creating a temporary DFT energies JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_dft_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_dft_energies_success(temp_dft_file, mock_dft_data):
    """Test successful loading of DFT energies."""
    # Patch the global path to point to our temp file
    with patch('code.data.dft_energy_mapper.DFT_ENERGIES_PATH', Path(temp_dft_file)):
        data = load_dft_energies()
        assert data == mock_dft_data

def test_load_dft_energies_file_not_found():
    """Test error handling when DFT file is missing."""
    with patch('code.data.dft_energy_mapper.DFT_ENERGIES_PATH', Path('/nonexistent/path.json')):
        with pytest.raises(DataLoadError, match="DFT energies file not found"):
            load_dft_energies()

def test_load_dft_energies_invalid_json(temp_dft_file):
    """Test error handling for invalid JSON."""
    # Write invalid JSON
    with open(temp_dft_file, 'w') as f:
        f.write("{ invalid json }")
    
    with patch('code.data.dft_energy_mapper.DFT_ENERGIES_PATH', Path(temp_dft_file)):
        with pytest.raises(DataLoadError, match="Failed to parse DFT energies JSON"):
            load_dft_energies()

def test_map_supercell_to_dft_energy_direct_match(mock_dft_data):
    """Test direct lookup of a supercell ID."""
    result = map_supercell_to_dft_energy('sigma5_fe_cr.cif', mock_dft_data)
    assert result['system'] == 'Fe-Cr'
    assert result['energy_eV'] == -0.15

def test_map_supercell_to_dft_energy_no_extension(mock_dft_data):
    """Test lookup without file extension."""
    result = map_supercell_to_dft_energy('sigma5_fe_cr', mock_dft_data)
    assert result['system'] == 'Fe-Cr'

def test_map_supercell_to_dft_energy_case_insensitive(mock_dft_data):
    """Test case-insensitive lookup."""
    result = map_supercell_to_dft_energy('SIGMA5_FE_CR.cif', mock_dft_data)
    assert result['system'] == 'Fe-Cr'

def test_map_supercell_to_dft_energy_key_normalization(mock_dft_data):
    """Test lookup with normalized keys (hyphen vs underscore)."""
    # Add a key with hyphens
    mock_data_hyphen = {'sigma5-fe-cr': {'system': 'Fe-Cr', 'energy_eV': -0.15}}
    result = map_supercell_to_dft_energy('sigma5_fe_cr.cif', mock_data_hyphen)
    assert result['system'] == 'Fe-Cr'

def test_map_supercell_to_dft_energy_not_found(mock_dft_data):
    """Test error handling when no matching entry is found."""
    with pytest.raises(DataLoadError, match="No DFT energy entry found"):
        map_supercell_to_dft_energy('sigma99_nonexistent.cif', mock_dft_data)

def test_map_supercell_to_dft_energy_empty_data():
    """Test error handling with empty DFT data."""
    with pytest.raises(DataLoadError, match="No DFT energy entry found"):
        map_supercell_to_dft_energy('sigma5_fe_cr.cif', {})