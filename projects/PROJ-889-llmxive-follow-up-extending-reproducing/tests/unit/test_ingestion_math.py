"""
Unit tests for G(t) and dG(t) calculation logic in code/ingestion.py.

These tests verify the mathematical correctness of the divergence gap 
and its derivative calculations.
"""
import pytest
import pandas as pd
import numpy as np
from code.ingestion import compute_divergence_gap, compute_derivative_and_zscore
from code.utils.math_utils import safe_z_score

class TestComputeDivergenceGap:
    def test_basic_divergence_calculation(self):
        """Test G(t) = |J_biased - J_unbiased|"""
        data = {
            'J_biased': [10.0, 20.0, 30.0],
            'J_unbiased': [8.0, 22.0, 25.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_divergence_gap(df)
        
        expected_G = [2.0, 2.0, 5.0]
        assert np.allclose(result['G_t'].values, expected_G)
        
    def test_negative_values(self):
        """Test G(t) handles negative scores correctly"""
        data = {
            'J_biased': [-10.0, 5.0],
            'J_unbiased': [-12.0, 3.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_divergence_gap(df)
        
        # |(-10) - (-12)| = 2
        # |5 - 3| = 2
        expected_G = [2.0, 2.0]
        assert np.allclose(result['G_t'].values, expected_G)

class TestComputeDerivativeAndZscore:
    def test_derivative_calculation(self):
        """Test dG(t) = G(t) - G(t-1)"""
        # Create a DataFrame with G_t already computed
        data = {
            'G_t': [2.0, 4.0, 7.0, 5.0],
            'timestep': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=2, min_samples=2)
        
        # dG[0] = 0 (no previous)
        # dG[1] = 4 - 2 = 2
        # dG[2] = 7 - 4 = 3
        # dG[3] = 5 - 7 = -2
        expected_dG = [0.0, 2.0, 3.0, -2.0]
        assert np.allclose(result['dG_t'].values, expected_dG)
        
    def test_zscore_zero_variance(self):
        """Test that z-score is 0 when variance is zero (safe_z_score logic)"""
        # Constant G_t values -> std = 0
        data = {
            'G_t': [5.0, 5.0, 5.0, 5.0],
            'timestep': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=3, min_samples=2)
        
        # Z-score should be 0 for all rows because std is 0
        assert all(result['z_score_G'] == 0.0)
        
    def test_zscore_normal_case(self):
        """Test z-score calculation with normal variance"""
        # Simple sequence: mean=2, std approx 1.41 (for 1, 2, 3)
        # We just check it produces a number and isn't NaN/Inf
        data = {
            'G_t': [1.0, 2.0, 3.0, 4.0],
            'timestep': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=3, min_samples=2)
        
        # The first few rows might be NaN due to min_samples, but later ones should be valid
        # Check that we don't have NaN in the last row
        assert not np.isnan(result['z_score_G'].iloc[-1])
        
    def test_min_samples_constraint(self):
        """Test that z-score is NaN/0 if min_samples not met"""
        data = {
            'G_t': [1.0, 2.0],
            'timestep': [1, 2]
        }
        df = pd.DataFrame(data)
        
        # Request min_samples=3, but we only have 2
        result = compute_derivative_and_zscore(df, window_size=5, min_samples=3)
        
        # With min_samples=3 and only 2 rows, rolling std should be NaN or handled
        # The safe_z_score logic should handle the NaN std, returning 0
        # Check that the result is not NaN (it should be 0 due to safe_z_score)
        assert not np.isnan(result['z_score_G']).all()
        # Specifically, if min_samples > available, rolling std is NaN, safe_z_score returns 0
        assert all(result['z_score_G'] == 0.0)

class TestSafeZScoreImport:
    """Verify safe_z_score is imported and works as expected in isolation"""
    def test_safe_z_score_zero_std(self):
        """Direct test of safe_z_score utility"""
        val = 5.0
        mean = 5.0
        std = 0.0
        
        result = safe_z_score(val, mean, std)
        assert result == 0.0
        
    def test_safe_z_score_normal(self):
        """Direct test of safe_z_score utility"""
        val = 10.0
        mean = 5.0
        std = 2.0
        
        result = safe_z_score(val, mean, std)
        assert result == 2.5
