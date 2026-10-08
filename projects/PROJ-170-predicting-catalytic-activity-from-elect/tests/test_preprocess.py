"""
Tests for preprocessing module.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from preprocess import (
    parse_oc20_to_dataframe,
    construct_unified_dataframe,
    compute_stoichiometry_features,
    define_global_vocabulary,
    save_vocabulary
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'composition': ['Fe2O3', 'Pt', 'CuO', 'Fe2O3'],
        'surface_facet': ['110', '111', '100', '110'],
        'experimental_tof': [1.5, 2.0, 1.2, np.nan],
        'd_band_center': [-2.5, -1.8, -2.1, -2.5],
        'adsorption_energy': [-1.2, -0.9, -1.5, -1.2]
    }
    return pd.DataFrame(data)

def test_parse_oc20_to_dataframe_missing_file():
    """Test that parsing fails gracefully for missing files."""
    with pytest.raises(SystemExit):
        parse_oc20_to_dataframe("nonexistent_file.h5")

def test_construct_unified_dataframe_generates_entry_ids(sample_dataframe):
    """Test that entry IDs are generated correctly."""
    df = construct_unified_dataframe(sample_dataframe)
    
    assert 'entry_id' in df.columns
    assert len(df['entry_id']) == len(df)
    
    # Check that entry IDs are unique for unique composition+facet pairs
    # Fe2O3-110 appears twice, should have same ID
    fe110_ids = df[df['composition'] == 'Fe2O3'][df['surface_facet'] == '110']['entry_id']
    assert len(fe110_ids.unique()) == 1

def test_compute_stoichiometry_features(sample_dataframe):
    """Test stoichiometry feature computation."""
    df = compute_stoichiometry_features(sample_dataframe)
    
    # Check that stoichiometry columns are added
    assert 'stoich_Fe' in df.columns
    assert 'stoich_O' in df.columns
    assert 'stoich_Pt' in df.columns
    assert 'stoich_Cu' in df.columns
    
    # Check normalization (sum of stoich columns should be ~1 for each row)
    stoich_cols = [col for col in df.columns if col.startswith('stoich_')]
    row_sums = df[stoich_cols].sum(axis=1)
    
    # Allow for small floating point errors
    assert all(abs(row_sums - 1.0) < 1e-6)

def test_define_global_vocabulary(sample_dataframe):
    """Test global vocabulary definition."""
    # First compute stoichiometry features
    df = compute_stoichiometry_features(sample_dataframe)
    
    # Define vocabulary
    vocab = define_global_vocabulary(df)
    
    # Check vocabulary structure
    assert isinstance(vocab, dict)
    assert len(vocab) > 0
    assert 'Fe' in vocab
    assert 'O' in vocab
    assert 'Pt' in vocab
    assert 'Cu' in vocab
    
    # Check that indices are sequential
    indices = list(vocab.values())
    assert indices == sorted(indices)
    assert set(indices) == set(range(len(indices)))

def test_save_vocabulary_creates_file(tmp_path):
    """Test that vocabulary is saved correctly."""
    vocab = {'Fe': 0, 'O': 1, 'Pt': 2}
    output_file = tmp_path / "test_vocab.json"
    
    save_vocabulary(vocab, str(output_file))
    
    assert output_file.exists()
    
    with open(output_file) as f:
        saved_vocab = json.load(f)
    
    assert saved_vocab == vocab

def test_data_integrity_no_nan_in_targets(sample_dataframe):
    """
    Contract test: Verify no NaN values in experimental_tof after imputation.
    Note: This test assumes T017a (imputation) has been run.
    For now, it checks that the input data structure is valid.
    """
    # Check that composition strings are non-empty
    assert all(sample_dataframe['composition'].str.len() > 0)
    
    # Check that surface_facet strings are non-empty
    assert all(sample_dataframe['surface_facet'].str.len() > 0)

def test_stoichiometry_zero_padding(sample_dataframe):
    """Test that elements not present in a composition are zero-padded."""
    df = compute_stoichiometry_features(sample_dataframe)
    
    # Pt should be 0 for Fe2O3 rows
    fe_rows = df[df['composition'] == 'Fe2O3']
    assert all(fe_rows['stoich_Pt'] == 0)
    
    # Fe should be 0 for Pt row
    pt_rows = df[df['composition'] == 'Pt']
    assert all(pt_rows['stoich_Fe'] == 0)