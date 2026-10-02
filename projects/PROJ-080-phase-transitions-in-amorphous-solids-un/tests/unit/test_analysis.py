import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from analysis import aggregate_to_shear_bands, perform_ks_test, apply_bonferroni_correction, aggregate_to_shear_bands_from_df

class TestAggregateToShearBands:
    def test_aggregate_basic(self):
        """Test basic aggregation with k=3."""
        # Create synthetic data
        np.random.seed(42)
        data = {
            'D2_min': np.random.rand(100),
            'label': [0] * 50 + [1] * 50,
            'trajectory_id': ['traj1'] * 50 + ['traj2'] * 50
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            result = aggregate_to_shear_bands_from_df(df, output_path, k=3)
            
            assert 'shear_band_id' in result.columns
            assert 'mean_D2_min' in result.columns
            assert 'particle_count' in result.columns
            assert len(result) == 3  # k=3
            assert result['particle_count'].sum() == 100
            
            # Check file was written
            assert os.path.exists(output_path)
            loaded = pd.read_csv(output_path)
            assert len(loaded) == 3

    def test_aggregate_insufficient_data(self):
        """Test behavior with insufficient data points."""
        data = {
            'D2_min': [0.1, 0.2],
            'label': [0, 0],
            'trajectory_id': ['traj1', 'traj1']
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.csv")
            # Should not raise, but adjust k
            result = aggregate_to_shear_bands_from_df(df, output_path, k=3)
            
            # Should have max(1, N) clusters
            assert len(result) <= 2

class TestKSTest:
    def test_ks_test_basic(self):
        """Test KS test calculation."""
        brittle_data = pd.DataFrame({'mean_D2_min': [0.1, 0.2, 0.3, 0.4, 0.5]})
        ductile_data = pd.DataFrame({'mean_D2_min': [0.6, 0.7, 0.8, 0.9, 1.0]})
        
        stat, pval = perform_ks_test(brittle_data, ductile_data)
        
        assert isinstance(stat, float)
        assert isinstance(pval, float)
        assert 0 <= stat <= 1
        assert 0 <= pval <= 1

    def test_ks_test_empty(self):
        """Test KS test with empty data."""
        with pytest.raises(ValueError):
            perform_ks_test(pd.DataFrame(), pd.DataFrame())

class TestBonferroni:
    def test_bonferroni_single_test(self):
        """Test Bonferroni with single test (no correction)."""
        p = 0.05
        corrected = apply_bonferroni_correction(p, 1)
        assert corrected == p

    def test_bonferroni_multiple_tests(self):
        """Test Bonferroni with multiple tests."""
        p = 0.01
        n = 5
        corrected = apply_bonferroni_correction(p, n)
        assert corrected == p * n
        assert corrected <= 1.0

    def test_bonferroni_cap(self):
        """Test Bonferroni caps at 1.0."""
        p = 0.5
        n = 3
        corrected = apply_bonferroni_correction(p, n)
        assert corrected == 1.0
