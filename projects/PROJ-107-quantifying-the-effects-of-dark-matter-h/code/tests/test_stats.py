"""
Unit tests for statistical analysis functions in stats.py.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.stats import (
    kruskal_wallis_test,
    mann_whitney_u_test,
    ks_test,
    bin_halo_by_shape,
    apply_bonferroni_correction,
    run_binning_tests
)

class TestBonferroniCorrection:
    """Tests for Bonferroni correction function."""

    def test_bonferroni_correction(self):
        """Test Bonferroni correction scales p-values correctly."""
        p_values = [0.01, 0.05, 0.10]
        adjusted = apply_bonferroni_correction(p_values, alpha=0.05)
        
        assert len(adjusted) == 3
        # With 3 tests, p=0.01 becomes 0.03
        assert adjusted[0] == pytest.approx(0.03, rel=1e-5)
        # p=0.05 becomes 0.15
        assert adjusted[1] == pytest.approx(0.15, rel=1e-5)

    def test_bonferroni_capped_at_one(self):
        """Test Bonferroni correction caps at 1.0."""
        p_values = [0.5, 0.6, 0.7, 0.8]  # 4 tests
        adjusted = apply_bonferroni_correction(p_values)
        
        # 0.8 * 4 = 3.2 -> capped at 1.0
        assert adjusted[3] == 1.0

class TestNonParametricTests:
    """Tests for Kruskal-Wallis, Mann-Whitney U, and KS tests."""

    def test_kruskal_wallis_test(self):
        """Test Kruskal-Wallis test returns valid statistics."""
        # Create three groups with different means
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(2, 1, 50)
        group3 = np.random.normal(4, 1, 50)
        
        H, p_value = kruskal_wallis_test([group1, group2, group3])
        
        assert H >= 0
        assert 0 <= p_value <= 1
        # With different means, p should be small
        assert p_value < 0.05

    def test_mann_whitney_u_test(self):
        """Test Mann-Whitney U test returns valid statistics."""
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(2, 1, 50)
        
        U, p_value = mann_whitney_u_test(group1, group2)
        
        assert U >= 0
        assert 0 <= p_value <= 1
        # With different means, p should be small
        assert p_value < 0.05

    def test_ks_test(self):
        """Test KS test returns valid statistics."""
        group1 = np.random.normal(0, 1, 50)
        group2 = np.random.normal(2, 1, 50)
        
        D, p_value = ks_test(group1, group2)
        
        assert 0 <= D <= 1
        assert 0 <= p_value <= 1
        # With different distributions, p should be small
        assert p_value < 0.05

    def test_empty_groups_raise_error(self):
        """Test that empty groups raise ValueError."""
        with pytest.raises(ValueError):
            kruskal_wallis_test([np.array([]), np.array([1, 2, 3])])
        
        with pytest.raises(ValueError):
            mann_whitney_u_test(np.array([]), np.array([1, 2, 3]))
        
        with pytest.raises(ValueError):
            ks_test(np.array([]), np.array([1, 2, 3]))

class TestShapeBinningLogic:
    """Tests for shape binning logic."""

    def test_bin_halo_by_shape(self):
        """Test shape binning thresholds."""
        assert bin_halo_by_shape(0.3) == 'prolate'
        assert bin_halo_by_shape(0.49) == 'prolate'
        assert bin_halo_by_shape(0.5) == 'triaxial'
        assert bin_halo_by_shape(0.6) == 'triaxial'
        assert bin_halo_by_shape(0.8) == 'triaxial'
        assert bin_halo_by_shape(0.81) == 'spherical'
        assert bin_halo_by_shape(1.0) == 'spherical'

    def test_run_binning_tests(self):
        """Test run_binning_tests produces expected output structure."""
        # Create synthetic matched data for testing
        np.random.seed(42)
        data = pd.DataFrame({
            'halo_id': range(100),
            'c_a_ratio': np.random.uniform(0.3, 1.0, 100),
            'sfr': np.random.normal(0, 1, 100),
            'mass': np.random.normal(10, 1, 100)
        })
        
        results = run_binning_tests(data)
        
        # Check that results are not empty
        assert not results.empty
        assert 'test' in results.columns
        assert 'statistic' in results.columns
        assert 'p_value' in results.columns
        assert 'groups_compared' in results.columns

        # Check that we have at least one Kruskal-Wallis result
        kw_results = results[results['test'] == 'kruskal_wallis']
        assert len(kw_results) >= 1

        # Check that we have MWU results for pairwise comparisons
        mwu_results = results[results['test'] == 'mann_whitney_u']
        assert len(mwu_results) >= 3  # 3 pairs

        # Check that we have KS results for pairwise comparisons
        ks_results = results[results['test'] == 'ks_test']
        assert len(ks_results) >= 3  # 3 pairs
