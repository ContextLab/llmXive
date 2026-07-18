"""
Unit tests for ingestion math logic (G(t), dG(t), z-score).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import compute_divergence_gap, compute_derivative_and_zscore

class TestDivergenceGap:
    def test_g_t_basic_calculation(self):
        """Test basic G(t) = |J_biased - J_unbiased| calculation."""
        data = {
            'step': [1, 2, 3],
            'reward_biased': [10.0, 20.0, 30.0],
            'reward_unbiased': [8.0, 15.0, 35.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_divergence_gap(df)
        
        expected_g_t = [2.0, 5.0, 5.0]
        assert np.allclose(result['G_t'].values, expected_g_t)

    def test_g_t_handles_nan_gracefully(self):
        """Test that G(t) calculation handles NaNs without crashing."""
        data = {
            'step': [1, 2, 3],
            'reward_biased': [10.0, np.nan, 30.0],
            'reward_unbiased': [8.0, 15.0, 35.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_divergence_gap(df)
        
        # First and third should be calculated, second should be NaN
        assert not np.isnan(result['G_t'].iloc[0])
        assert np.isnan(result['G_t'].iloc[1])
        assert not np.isnan(result['G_t'].iloc[2])

class TestDerivativeAndZscore:
    def test_dg_t_derivative_calculation(self):
        """Test Delta G(t) = G(t) - G(t-1) calculation."""
        data = {
            'step': [1, 2, 3, 4],
            'G_t': [2.0, 5.0, 5.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=2)
        
        # First row should be NaN (no previous step)
        assert np.isnan(result['dG_t'].iloc[0])
        # Subsequent rows
        assert result['dG_t'].iloc[1] == 3.0  # 5 - 2
        assert result['dG_t'].iloc[2] == 0.0  # 5 - 5
        assert result['dG_t'].iloc[3] == 5.0  # 10 - 5

    def test_zscore_zero_variance(self):
        """Test that z-score is 0 when variance is zero."""
        # Constant G_t values
        data = {
            'step': [1, 2, 3, 4, 5],
            'G_t': [5.0, 5.0, 5.0, 5.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=3)
        
        # Z-score should be 0 for all rows due to zero variance
        assert all(result['G_t_zscore'] == 0.0)

    def test_zscore_normal_case(self):
        """Test z-score calculation in a normal case."""
        # Create a sequence with a known mean and std
        # [2, 4, 6, 8, 10] -> mean=6, std=2.828
        data = {
            'step': [1, 2, 3, 4, 5],
            'G_t': [2.0, 4.0, 6.0, 8.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_derivative_and_zscore(df, window_size=5)
        
        # Check that z-scores are not all zero and follow expected pattern
        z_scores = result['G_t_zscore'].values
        assert not all(z_scores == 0.0)
        # The middle value (6) should have z-score close to 0
        assert abs(z_scores[2]) < 0.5
