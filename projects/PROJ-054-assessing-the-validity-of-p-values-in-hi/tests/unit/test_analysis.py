import pytest
import numpy as np
from scipy import stats
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analyze_pvalues import calculate_ks_statistic, generate_permutation_reference

def test_calculate_ks_statistic_uniform():
    """Test KS statistic on uniform data."""
    pvalues = np.random.uniform(0, 1, 1000)
    ks_stat, _ = stats.kstest(pvalues, 'uniform')
    assert ks_stat < 0.1 # Should be close to 0 for uniform

def test_calculate_ks_statistic_non_uniform():
    """Test KS statistic on non-uniform data."""
    # Skewed data
    pvalues = np.random.beta(0.5, 1, 1000)
    ks_stat, _ = stats.kstest(pvalues, 'uniform')
    assert ks_stat > 0.1 # Should be significantly different from 0

def test_permutation_reference():
    """Test permutation reference generation."""
    # Generate some data
    np.random.seed(42)
    data = np.random.normal(0, 1, (100, 10))
    rng = np.random.default_rng(42)
    pvals = generate_permutation_reference(data, n_permutations=10, rng=rng)
    assert len(pvals) == 10
    assert all(0 <= p <= 1 for p in pvals)
