"""
Unit tests for compute_stratum_means functionality.

Tests verify:
1. Mean computation per stratum
2. CLR transformation correctness
3. Output format validation
"""

import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from compute_stratum_means import (
    compute_stratum_means,
    clr_transform,
    apply_clr_to_stratum_means,
    format_output
)

@pytest.fixture
def sample_raw_data():
    """Create sample raw stratum aggregation data for testing."""
    data = {
        'stratum_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S3', 'S3', 'S3', 'S3'],
        'alpha_power': [10.0, 12.0, 11.0, 15.0, 16.0, 8.0, 9.0, 10.0, 11.0],
        'taxon_A': [0.1, 0.2, 0.15, 0.3, 0.25, 0.05, 0.08, 0.06, 0.07],
        'taxon_B': [0.4, 0.35, 0.38, 0.2, 0.18, 0.5, 0.48, 0.49, 0.51],
        'taxon_C': [0.5, 0.45, 0.47, 0.5, 0.57, 0.45, 0.44, 0.45, 0.42]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_stratum_means(sample_raw_data):
    """Create pre-computed stratum means for testing CLR."""
    # Manually compute means for testing
    means = sample_raw_data.groupby('stratum_id').mean().reset_index()
    means['n_subjects'] = sample_raw_data.groupby('stratum_id').size().values
    return means

def test_compute_stratum_means_basic(sample_raw_data):
    """Test basic mean computation per stratum."""
    result = compute_stratum_means(sample_raw_data)
    
    # Check that we have 3 strata
    assert len(result) == 3
    
    # Check that stratum S1 mean alpha is correct (10+12+11)/3 = 11.0
    s1_row = result[result['stratum_id'] == 'S1'].iloc[0]
    assert np.isclose(s1_row['alpha_power'], 11.0, rtol=1e-5)
    
    # Check n_subjects
    assert s1_row['n_subjects'] == 3
    
    # Check taxon means
    assert np.isclose(s1_row['taxon_A'], 0.15, rtol=1e-5)
    assert np.isclose(s1_row['taxon_B'], 0.376666, rtol=1e-3)

def test_clr_transform_basic():
    """Test CLR transformation with simple values."""
    abundances = pd.Series([0.1, 0.2, 0.3, 0.4])
    pseudocount = 0.5
    
    result = clr_transform(abundances, pseudocount)
    
    # CLR values should sum to approximately 0 (property of CLR)
    assert np.isclose(result.sum(), 0.0, rtol=1e-5)
    
    # All values should be finite
    assert np.all(np.isfinite(result))

def test_clr_transform_with_zeros():
    """Test CLR transformation handles zero values with pseudocount."""
    abundances = pd.Series([0.0, 0.1, 0.2, 0.3])
    pseudocount = 0.5
    
    result = clr_transform(abundances, pseudocount)
    
    # Should not raise an error
    assert len(result) == 4
    assert np.all(np.isfinite(result))

def test_apply_clr_to_stratum_means(sample_stratum_means):
    """Test CLR application to stratum means DataFrame."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    pseudocount = 0.5
    
    result = apply_clr_to_stratum_means(sample_stratum_means, taxa_cols, pseudocount)
    
    # Check that CLR values sum to ~0 for each stratum
    for stratum_id in result['stratum_id'].unique():
        stratum_row = result[result['stratum_id'] == stratum_id].iloc[0]
        clr_sum = sum(stratum_row[col] for col in taxa_cols)
        assert np.isclose(clr_sum, 0.0, rtol=1e-3)

def test_format_output(sample_stratum_means):
    """Test output formatting."""
    taxa_cols = ['taxon_A', 'taxon_B', 'taxon_C']
    pseudocount = 0.5
    
    # First apply CLR
    clr_df = apply_clr_to_stratum_means(sample_stratum_means, taxa_cols, pseudocount)
    
    # Then format
    formatted = format_output(clr_df, 'stratum_id', 'alpha_power', taxa_cols)
    
    # Check columns
    assert 'stratum_id' in formatted.columns
    assert 'mean_alpha_power' in formatted.columns
    assert 'clr_taxa_abundances' in formatted.columns
    assert 'n_subjects' in formatted.columns
    
    # Check that clr_taxa_abundances is a dict
    for _, row in formatted.iterrows():
        assert isinstance(row['clr_taxa_abundances'], dict)
        assert len(row['clr_taxa_abundances']) == len(taxa_cols)

def test_compute_stratum_means_empty_stratum():
    """Test handling of edge cases."""
    data = {
        'stratum_id': ['S1', 'S1'],
        'alpha_power': [10.0, 10.0],
        'taxon_A': [0.5, 0.5],
        'taxon_B': [0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    result = compute_stratum_means(df)
    
    assert len(result) == 1
    assert result['n_subjects'].iloc[0] == 2

def test_compute_stratum_means_single_subject():
    """Test with single subject per stratum."""
    data = {
        'stratum_id': ['S1', 'S2', 'S3'],
        'alpha_power': [10.0, 12.0, 15.0],
        'taxon_A': [0.1, 0.2, 0.3],
        'taxon_B': [0.9, 0.8, 0.7]
    }
    df = pd.DataFrame(data)
    
    result = compute_stratum_means(df)
    
    assert len(result) == 3
    assert all(result['n_subjects'] == 1)