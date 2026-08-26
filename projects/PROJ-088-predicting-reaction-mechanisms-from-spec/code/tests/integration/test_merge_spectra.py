"""
Integration tests for merge_spectra.py module.

Tests the end-to-end merging of IR and NMR data into fingerprints.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.merge_spectra import (
    bin_spectrum_ir, 
    bin_spectrum_nmr, 
    merge_and_bin_spectra, 
    validate_fingerprints,
    validate_class_balance
)
from src.utils.io import write_json_file

@pytest.fixture
def sample_nist_data():
    """Create sample NIST IR data for testing."""
    return pd.DataFrame({
        'compound_id': ['C001', 'C002', 'C003'],
        'mechanism_label': ['SN2', 'SN1', 'E1'],
        'frequencies_ir': [
            [1000, 1500, 2000, 2500, 3000],
            [1000, 1500, 2000, 2500, 3000],
            [1000, 1500, 2000, 2500, 3000]
        ],
        'intensities_ir': [
            [0.1, 0.5, 0.8, 0.3, 0.2],
            [0.2, 0.6, 0.9, 0.4, 0.3],
            [0.15, 0.55, 0.85, 0.35, 0.25]
        ]
    })

@pytest.fixture
def sample_pubchem_data():
    """Create sample PubChem NMR data for testing."""
    return pd.DataFrame({
        'compound_id': ['C001', 'C002', 'C003'],
        'chemical_shifts_nmr': [
            [0, 2, 4, 6, 8, 10, 12],
            [0, 2, 4, 6, 8, 10, 12],
            [0, 2, 4, 6, 8, 10, 12]
        ],
        'intensities_nmr': [
            [0.1, 0.3, 0.5, 0.7, 0.6, 0.4, 0.2],
            [0.15, 0.35, 0.55, 0.75, 0.65, 0.45, 0.25],
            [0.12, 0.32, 0.52, 0.72, 0.62, 0.42, 0.22]
        ]
    })

@pytest.fixture
def sample_bin_mapping():
    """Create sample bin mapping configuration."""
    return {
        'bins': {
            'IR': {
                'count': 10,
                'edges': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
                'method': 'linear_interpolation'
            },
            'NMR': {
                'count': 6,
                'edges': [0, 2, 4, 6, 8, 10, 12],
                'method': 'linear_interpolation'
            }
        }
    }

def test_bin_spectrum_ir(sample_bin_mapping):
    """Test IR spectrum binning."""
    spectrum_data = {
        'frequencies': [1000, 1500, 2000],
        'intensities': [0.1, 0.5, 0.9]
    }
    
    result = bin_spectrum_ir(spectrum_data, sample_bin_mapping)
    
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == sample_bin_mapping['bins']['IR']['count']
    assert not np.any(np.isnan(result))

def test_bin_spectrum_nmr(sample_bin_mapping):
    """Test NMR spectrum binning."""
    spectrum_data = {
        'chemical_shifts': [0, 4, 8, 12],
        'intensities': [0.1, 0.5, 0.8, 0.2]
    }
    
    result = bin_spectrum_nmr(spectrum_data, sample_bin_mapping)
    
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert len(result) == sample_bin_mapping['bins']['NMR']['count']
    assert not np.any(np.isnan(result))

def test_merge_and_bin_spectra(sample_nist_data, sample_pubchem_data, sample_bin_mapping):
    """Test merging and binning of spectra."""
    result_df = merge_and_bin_spectra(sample_nist_data, sample_pubchem_data, sample_bin_mapping)
    
    assert len(result_df) > 0
    assert 'fingerprint' in result_df.columns
    assert 'mechanism_label' in result_df.columns
    
    # Check fingerprint dimensions (IR bins + NMR bins)
    expected_dim = (
        sample_bin_mapping['bins']['IR']['count'] + 
        sample_bin_mapping['bins']['NMR']['count']
    )
    
    for idx, row in result_df.iterrows():
        fp = row['fingerprint']
        assert len(fp) == expected_dim
        assert not np.any(np.isnan(fp))

def test_validate_fingerprints(sample_nist_data, sample_pubchem_data, sample_bin_mapping):
    """Test fingerprint validation."""
    result_df = merge_and_bin_spectra(sample_nist_data, sample_pubchem_data, sample_bin_mapping)
    
    assert validate_fingerprints(result_df) is True

def test_empty_fingerprint_validation(sample_bin_mapping):
    """Test validation with empty dataframe."""
    empty_df = pd.DataFrame()
    
    # Should handle empty dataframe gracefully
    assert validate_fingerprints(empty_df) is True

def test_edge_case_no_matching_nmr(sample_nist_data, sample_bin_mapping):
    """Test merge when no NMR data matches."""
    # Create NMR data with different compound IDs
    no_match_pubchem = pd.DataFrame({
        'compound_id': ['X001', 'X002'],
        'chemical_shifts_nmr': [[0, 2, 4], [0, 2, 4]],
        'intensities_nmr': [[0.1, 0.5, 0.9], [0.1, 0.5, 0.9]]
    })
    
    result_df = merge_and_bin_spectra(sample_nist_data, no_match_pubchem, sample_bin_mapping)
    
    # Should return empty dataframe
    assert len(result_df) == 0

def test_class_balance_validation(sample_nist_data, sample_pubchem_data, sample_bin_mapping):
    """Test class balance calculation."""
    result_df = merge_and_bin_spectra(sample_nist_data, sample_pubchem_data, sample_bin_mapping)
    
    metrics = validate_class_balance(result_df)
    
    assert 'total_samples' in metrics
    assert 'class_counts' in metrics
    assert 'class_balance_ratio' in metrics
    
    # Check that we have all three classes
    assert 'SN1' in metrics['class_counts']
    assert 'SN2' in metrics['class_counts']
    assert 'E1' in metrics['class_counts']