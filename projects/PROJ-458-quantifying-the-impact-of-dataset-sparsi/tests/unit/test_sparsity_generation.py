"""
Unit tests for sparsity_generation.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.sparsity_generation import (
    load_rss_pool,
    compute_elemental_fingerprints,
    generate_stratified_subsets,
    validate_stratification
)
from code.utils.data_models import SparsitySubset

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'material_id': ['mp-1', 'mp-2', 'mp-3', 'mp-4', 'mp-5'],
        'composition': ['Fe2O3', 'SiO2', 'Al2O3', 'Fe3O4', 'NaCl'],
        'formation_energy': [-1.0, -2.0, -1.5, -1.2, -0.5],
        'dft_computed': [True, True, True, True, True]
    }
    return pd.DataFrame(data)

def test_load_rss_pool_missing_file():
    """Test that load_rss_pool raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_rss_pool("nonexistent_file.csv")

def test_compute_elemental_fingerprints(sample_df):
    """Test elemental fingerprint computation."""
    fingerprints = compute_elemental_fingerprints(sample_df)
    
    assert isinstance(fingerprints, np.ndarray)
    assert fingerprints.shape[0] == len(sample_df)
    assert fingerprints.shape[1] > 0  # At least one element
    
    # Check that fingerprints are non-negative
    assert np.all(fingerprints >= 0)

def test_generate_stratified_subsets(sample_df):
    """Test stratified subset generation."""
    fingerprints = compute_elemental_fingerprints(sample_df)
    levels = [0.5, 0.8]
    seeds = [42]
    
    subsets = generate_stratified_subsets(
        sample_df, fingerprints, levels, seeds
    )
    
    assert len(subsets) == len(levels) * len(seeds)
    
    for subset_df, metadata in subsets:
        assert isinstance(subset_df, pd.DataFrame)
        assert isinstance(metadata, SparsitySubset)
        assert metadata.percentage in [50.0, 80.0]
        assert metadata.seed == 42
        assert len(subset_df) <= len(sample_df)

def test_validate_stratification(sample_df):
    """Test stratification validation."""
    # Create a subset
    subset_df = sample_df.sample(frac=0.8, random_state=42)
    
    validation = validate_stratification(sample_df, subset_df)
    
    assert "ks_statistic" in validation
    assert "ks_p_value" in validation
    assert "js_divergence" in validation
    assert "distribution_preserved" in validation
    
    assert isinstance(validation["ks_statistic"], float)
    assert isinstance(validation["ks_p_value"], float)
    assert isinstance(validation["js_divergence"], float)
    assert isinstance(validation["distribution_preserved"], bool)

def test_sparsity_subset_model():
    """Test SparsitySubset dataclass."""
    subset = SparsitySubset(
        level=0.5,
        seed=42,
        percentage=50.0,
        checksum="abc123"
    )
    
    assert subset.level == 0.5
    assert subset.seed == 42
    assert subset.percentage == 50.0
    assert subset.checksum == "abc123"