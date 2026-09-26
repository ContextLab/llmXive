"""
Unit tests for permutation testing functionality (T024).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from permutation_test import run_permutation_test, DEFAULT_ITERATIONS
from seed_manager import set_seed

@pytest.fixture
def sample_stratum_data():
    """Create sample stratum data for testing."""
    np.random.seed(42)
    n_strata = 20
    
    data = {
        'stratum_id': [f'Stratum_{i}' for i in range(n_strata)],
        'mean_alpha_power': np.random.normal(10, 2, n_strata),
        'n_subjects': np.random.randint(5, 20, n_strata)
    }
    
    # Add CLR-transformed taxa abundances
    for i in range(10):
        data[f'taxon_{i}'] = np.random.normal(0, 1, n_strata)
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_top_taxa():
    """Return list of sample taxa names."""
    return [f'taxon_{i}' for i in range(10)]

def test_permutation_test_runs(sample_stratum_data, sample_top_taxa):
    """Test that permutation test runs without errors."""
    set_seed(42)
    
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=100,  # Reduced for testing
        seed=42
    )
    
    # Check results structure
    assert 'observed_stats' in results
    assert 'null_distribution' in results
    assert 'perm_test_passed' in results
    assert 'n_iterations' in results
    assert results['n_iterations'] == 100

def test_permutation_test_iterations(sample_stratum_data, sample_top_taxa):
    """Test that permutation test runs correct number of iterations."""
    set_seed(42)
    
    n_iters = 50
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=n_iters,
        seed=42
    )
    
    # Check null distribution shape
    assert null_dist.shape[0] == n_iters
    assert null_dist.shape[1] == len(sample_top_taxa)

def test_permutation_test_seed_reproducibility(sample_stratum_data, sample_top_taxa):
    """Test that permutation test is reproducible with same seed."""
    set_seed(42)
    
    null_dist1, results1 = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=50,
        seed=42
    )
    
    set_seed(42)
    
    null_dist2, results2 = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=50,
        seed=42
    )
    
    # Results should be identical
    np.testing.assert_array_almost_equal(null_dist1, null_dist2)
    assert results1['perm_test_passed'] == results2['perm_test_passed']

def test_permutation_test_insufficient_strata():
    """Test that permutation test fails with too few strata."""
    # Create data with only 2 strata
    data = pd.DataFrame({
        'stratum_id': ['S1', 'S2'],
        'mean_alpha_power': [10.0, 12.0],
        'taxon_0': [0.5, 0.6],
        'taxon_1': [0.3, 0.4]
    })
    
    with pytest.raises(ValueError, match="Insufficient strata"):
        run_permutation_test(
            stratum_data=data,
            top_taxa=['taxon_0', 'taxon_1'],
            n_iterations=10,
            seed=42
        )

def test_permutation_test_max_rho_computation(sample_stratum_data, sample_top_taxa):
    """Test that observed max rho is computed correctly."""
    set_seed(42)
    
    # Create data with known correlation
    sample_stratum_data['mean_alpha_power'] = sample_stratum_data['taxon_0'] * 2 + 5
    
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=10,
        seed=42
    )
    
    # Check that observed max rho is computed
    assert 'observed_max_rho' in results
    assert results['observed_max_rho'] > 0.5  # Should be high correlation

def test_permutation_test_null_distribution_shape(sample_stratum_data, sample_top_taxa):
    """Test that null distribution has correct shape."""
    n_taxa = len(sample_top_taxa)
    n_iters = 200
    
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=n_iters,
        seed=42
    )
    
    assert null_dist.shape == (n_iters, n_taxa)
    assert results['null_distribution'] is not None
    assert len(results['null_distribution']) == n_iters

def test_permutation_test_significance_threshold(sample_stratum_data, sample_top_taxa):
    """Test that significance thresholds are computed."""
    set_seed(42)
    
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=sample_top_taxa,
        n_iterations=100,
        seed=42
    )
    
    assert 'significance_thresholds' in results
    assert len(results['significance_thresholds']) == len(sample_top_taxa)
    assert all(t > 0 for t in results['significance_thresholds'])

def test_permutation_test_with_varying_variance(sample_stratum_data, sample_top_taxa):
    """Test handling of taxa with low variance."""
    # Create data with one constant taxon
    sample_stratum_data['taxon_constant'] = 5.0
    sample_stratum_data['taxon_varying'] = np.random.normal(0, 1, len(sample_stratum_data))
    
    taxa_to_test = ['taxon_constant', 'taxon_varying']
    
    set_seed(42)
    
    null_dist, results = run_permutation_test(
        stratum_data=sample_stratum_data,
        top_taxa=taxa_to_test,
        n_iterations=50,
        seed=42
    )
    
    # Should handle constant taxon gracefully
    assert 'observed_stats' in results
    assert results['n_iterations'] == 50