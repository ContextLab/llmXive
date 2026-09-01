"""
Unit tests for data ingestion logic.

Verifies:
- Filtering for FCC crystal structure
- Filtering for self-diffusion mode
- Unit conversion from kJ/mol to eV/atom
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from data.ingestion import load_and_filter, _standardize_units

@pytest.fixture
def mock_mixed_data():
    """Create a mock CSV with mixed crystal structures and diffusion modes."""
    data = {
        'element': ['Cu', 'Al', 'Fe', 'Ni', 'W', 'Mo'],
        'crystal_structure': ['FCC', 'FCC', 'BCC', 'FCC', 'BCC', 'HCP'],
        'diffusion_mode': ['self', 'solute', 'self', 'self', 'self', 'self'],
        'activation_energy_eV': [1.2, 0.8, 2.1, 1.5, 3.0, 2.5],
        'unit': ['eV/atom', 'eV/atom', 'kJ/mol', 'eV/atom', 'kJ/mol', 'eV/atom']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(mock_mixed_data):
    """Create a temporary CSV file with mock data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        mock_mixed_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_filter_fcc_only(temp_csv_file):
    """Test that only FCC crystal structure rows are retained."""
    result = load_and_filter(temp_csv_file)
    
    # Check that all rows are FCC
    assert all(result['crystal_structure'].str.upper() == 'FCC')
    
    # Check specific elements: Cu (FCC), Al (FCC), Ni (FCC) should be present
    # Fe (BCC), W (BCC), Mo (HCP) should be excluded
    expected_elements = {'Cu', 'Al', 'Ni'}
    assert set(result['element']) == expected_elements

def test_filter_self_diffusion_only(temp_csv_file):
    """Test that only self-diffusion mode rows are retained."""
    result = load_and_filter(temp_csv_file)
    
    # Check that all rows are self-diffusion
    assert all(result['diffusion_mode'].str.lower() == 'self')
    
    # Al was FCC but solute, so should be excluded
    assert 'Al' not in result['element'].values

def test_unit_conversion_kj_to_ev(temp_csv_file):
    """Test conversion from kJ/mol to eV/atom."""
    result = load_and_filter(temp_csv_file)
    
    # Check that all units are eV/atom
    assert all(result['unit'].str.lower() == 'eV/atom')
    
    # Fe had 2.1 kJ/mol, should be converted to 2.1 / 96.485
    fe_row = result[result['element'] == 'Fe']
    assert len(fe_row) == 1
    expected_ev = 2.1 / 96.485
    assert np.isclose(fe_row['activation_energy_eV'].values[0], expected_ev, rtol=1e-5)
    
    # W had 3.0 kJ/mol, should be converted
    w_row = result[result['element'] == 'W']
    assert len(w_row) == 1
    expected_ev_w = 3.0 / 96.485
    assert np.isclose(w_row['activation_energy_eV'].values[0], expected_ev_w, rtol=1e-5)

def test_standardize_units_function():
    """Test the _standardize_units helper function directly."""
    df = pd.DataFrame({
        'activation_energy_eV': [100.0, 200.0],
        'unit': ['kJ/mol', 'eV/atom']
    })
    
    result = _standardize_units(df)
    
    assert result['unit'].iloc[0] == 'eV/atom'
    assert result['unit'].iloc[1] == 'eV/atom'
    assert np.isclose(result['activation_energy_eV'].iloc[0], 100.0 / 96.485)
    assert result['activation_energy_eV'].iloc[1] == 200.0

def test_output_file_creation(temp_csv_file):
    """Test that output file is created when specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'filtered_output.csv'
        result = load_and_filter(temp_csv_file, str(output_path))
        
        assert output_path.exists()
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(result)
        assert list(saved_df.columns) == list(result.columns)

def test_case_insensitive_filtering():
    """Test that filtering is case-insensitive for structure and mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / 'case_test.csv'
        
        data = pd.DataFrame({
            'element': ['A', 'B', 'C', 'D'],
            'crystal_structure': ['fcc', 'FCC', 'Fcc', 'BCC'],
            'diffusion_mode': ['SELF', 'self', 'Self', 'SOLUTE'],
            'activation_energy_eV': [1.0, 2.0, 3.0, 4.0],
            'unit': ['eV/atom'] * 4
        })
        data.to_csv(temp_path, index=False)
        
        result = load_and_filter(str(temp_path))
        
        # All A, B, C should be included (all FCC variants), D excluded
        assert len(result) == 3
        assert set(result['element']) == {'A', 'B', 'C'}
        
        # All modes should be normalized to lowercase 'self'
        assert all(result['diffusion_mode'].str.lower() == 'self')