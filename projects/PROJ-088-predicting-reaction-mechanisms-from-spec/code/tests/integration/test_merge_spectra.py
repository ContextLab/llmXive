"""
Integration test for merge_spectra module.

Tests the end-to-end merging and binning of IR and NMR datasets.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.ingestion.merge_spectra import (
    bin_spectrum_ir,
    bin_spectrum_nmr,
    merge_and_bin_spectra,
    validate_fingerprints,
    NIST_BIN_COUNT,
    NMR_BIN_COUNT
)

@pytest.fixture
def sample_nist_data():
    """Create sample NIST IR data for testing."""
    data = {
        'compound_id': ['C001', 'C002'],
        'frequencies': [
            [500.0, 1000.0, 1500.0, 2000.0, 2500.0],
            [600.0, 1100.0, 1600.0, 2100.0, 2600.0]
        ],
        'intensities': [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6]
        ],
        'label': ['SN1', 'SN2'],
        'provenance': ['kinetic studies', 'kinetic studies']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_pubchem_data():
    """Create sample PubChem NMR data for testing."""
    data = {
        'compound_id': ['C001', 'C002'],
        'shifts': [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [1.5, 2.5, 3.5, 4.5, 5.5]
        ],
        'intensities': [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6]
        ],
        'provenance': ['kinetic studies', 'kinetic studies']
    }
    return pd.DataFrame(data)

def test_bin_spectrum_ir():
    """Test IR spectrum binning function."""
    frequencies = np.array([500.0, 1000.0, 1500.0, 2000.0, 2500.0])
    intensities = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    
    binned = bin_spectrum_ir(frequencies, intensities)
    
    assert len(binned) == NIST_BIN_COUNT
    assert np.sum(binned) > 0  # Should have some intensity
    assert np.all(binned >= 0)  # All values should be non-negative

def test_bin_spectrum_nmr():
    """Test NMR spectrum binning function."""
    shifts = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    intensities = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    
    binned = bin_spectrum_nmr(shifts, intensities)
    
    assert len(binned) == NMR_BIN_COUNT
    assert np.sum(binned) > 0  # Should have some intensity
    assert np.all(binned >= 0)  # All values should be non-negative

def test_merge_and_bin_spectra(sample_nist_data, sample_pubchem_data):
    """Test the merge and binning process."""
    merged_df = merge_and_bin_spectra(sample_nist_data, sample_pubchem_data)
    
    # Check that we have the expected number of records
    assert len(merged_df) == 2  # Both compounds should be merged
    
    # Check that fingerprints have the correct length
    for idx, row in merged_df.iterrows():
        fingerprint = np.array(row['fingerprint'])
        assert len(fingerprint) == NIST_BIN_COUNT + NMR_BIN_COUNT
        assert np.all(fingerprint >= 0)  # All values should be non-negative
    
    # Check that labels are preserved
    assert 'SN1' in merged_df['label'].values
    assert 'SN2' in merged_df['label'].values

def test_validate_fingerprints():
    """Test fingerprint validation function."""
    # Create a valid dataset
    valid_data = {
        'compound_id': ['C001'],
        'fingerprint': [np.random.rand(NIST_BIN_COUNT + NMR_BIN_COUNT).tolist()],
        'label': ['SN1'],
        'source': ['test']
    }
    valid_df = pd.DataFrame(valid_data)
    
    results = validate_fingerprints(valid_df)
    
    assert results['total_records'] == 1
    assert results['nan_count'] == 0
    assert results['empty_fingerprints'] == 0
    assert results['invalid_labels'] == 0
    assert len(results['issues']) == 0
    
    # Create an invalid dataset with NaN values
    invalid_data = {
        'compound_id': ['C002'],
        'fingerprint': [np.full(NIST_BIN_COUNT + NMR_BIN_COUNT, np.nan).tolist()],
        'label': ['SN1'],
        'source': ['test']
    }
    invalid_df = pd.DataFrame(invalid_data)
    
    results = validate_fingerprints(invalid_df)
    
    assert results['nan_count'] == 1
    assert len(results['issues']) == 1
    assert 'NaN values' in results['issues'][0]
    
    # Create a dataset with invalid labels
    invalid_label_data = {
        'compound_id': ['C003'],
        'fingerprint': [np.random.rand(NIST_BIN_COUNT + NMR_BIN_COUNT).tolist()],
        'label': ['INVALID'],
        'source': ['test']
    }
    invalid_label_df = pd.DataFrame(invalid_label_data)
    
    results = validate_fingerprints(invalid_label_df)
    
    assert results['invalid_labels'] == 1
    assert len(results['issues']) == 1
    assert 'Invalid label' in results['issues'][0]

def test_empty_fingerprint_validation():
    """Test validation of empty fingerprints."""
    empty_data = {
        'compound_id': ['C004'],
        'fingerprint': [np.zeros(NIST_BIN_COUNT + NMR_BIN_COUNT).tolist()],
        'label': ['SN1'],
        'source': ['test']
    }
    empty_df = pd.DataFrame(empty_data)
    
    results = validate_fingerprints(empty_df)
    
    assert results['empty_fingerprints'] == 1
    assert len(results['issues']) == 1
    assert 'Empty fingerprint' in results['issues'][0]

def test_edge_case_no_matching_nmr():
    """Test handling of compounds with no matching NMR data."""
    nist_data = pd.DataFrame({
        'compound_id': ['C001'],
        'frequencies': [[500.0, 1000.0]],
        'intensities': [[0.1, 0.2]],
        'label': ['SN1'],
        'provenance': ['kinetic studies']
    })
    
    pubchem_data = pd.DataFrame({
        'compound_id': ['C002'],  # Different compound
        'shifts': [[1.0, 2.0]],
        'intensities': [[0.1, 0.2]],
        'provenance': ['kinetic studies']
    })
    
    # Should handle gracefully and not include C001 in the result
    merged_df = merge_and_bin_spectra(nist_data, pubchem_data)
    
    assert len(merged_df) == 0  # No matching compounds

if __name__ == "__main__":
    pytest.main([__file__, "-v"])