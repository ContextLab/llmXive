import pytest
import pandas as pd
import numpy as np
from code.validation import bootstrap_resample, get_top_correlations

class TestBootstrapResample:
    def test_bootstrap_resample_size(self):
        """Test that bootstrap resample maintains the correct size."""
        df = pd.DataFrame({
            'var1': range(100),
            'var2': range(100, 200)
        })
        
        # Resample with replacement
        resampled = bootstrap_resample(df, n_iterations=100, seed=42)
        
        # Each resample should have the same size as original
        for i, sample in enumerate(resampled):
            assert len(sample) == len(df)
            assert sample.equals(resampled[i])  # Check consistency

    def test_bootstrap_resample_reproducibility(self):
        """Test that bootstrap resample is reproducible with same seed."""
        df = pd.DataFrame({
            'var1': range(100),
            'var2': range(100, 200)
        })
        
        # First run
        resampled1 = list(bootstrap_resample(df, n_iterations=5, seed=42))
        
        # Second run with same seed
        resampled2 = list(bootstrap_resample(df, n_iterations=5, seed=42))
        
        # Should be identical
        for i in range(5):
            pd.testing.assert_frame_equal(resampled1[i], resampled2[i])

class TestGetTopCorrelations:
    def test_get_top_correlations_count(self):
        """Test that get_top_correlations returns the correct number of results."""
        df = pd.DataFrame({
            'var1': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            'var2': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6],
            'var3': [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
            'var4': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9]
        })
        
        # Get top 2 correlations
        top = get_top_correlations(df, 'var1', n_top=2)
        
        assert len(top) == 2

    def test_get_top_correlations_ranking(self):
        """Test that get_top_correlations returns results in correct order."""
        # Create data with known correlation strengths
        np.random.seed(42)
        n = 100
        x = np.random.rand(n)
        
        # Strong positive correlation
        y1 = x * 0.9 + np.random.normal(0, 0.1, n)
        # Moderate positive correlation
        y2 = x * 0.5 + np.random.normal(0, 0.1, n)
        # Weak correlation
        y3 = x * 0.1 + np.random.normal(0, 0.1, n)
        
        df = pd.DataFrame({
            'var1': x,
            'var2': y1,
            'var3': y2,
            'var4': y3
        })
        
        top = get_top_correlations(df, 'var1', n_top=3)
        
        # Check that var2 (strongest) is first
        assert top.iloc[0]['variable'] == 'var2'
        # Check that var3 (moderate) is second
        assert top.iloc[1]['variable'] == 'var3'
        # Check that var4 (weakest) is third
        assert top.iloc[2]['variable'] == 'var4'

    def test_get_top_correlations_sign(self):
        """Test that get_top_correlations preserves correlation sign."""
        np.random.seed(42)
        n = 100
        x = np.random.rand(n)
        
        # Positive correlation
        y_pos = x * 0.8 + np.random.normal(0, 0.1, n)
        # Negative correlation
        y_neg = -x * 0.8 + np.random.normal(0, 0.1, n)
        
        df = pd.DataFrame({
            'var1': x,
            'var_pos': y_pos,
            'var_neg': y_neg
        })
        
        top = get_top_correlations(df, 'var1', n_top=2)
        
        # Check signs
        assert top.iloc[0]['correlation'] > 0  # Positive correlation first
        assert top.iloc[1]['correlation'] < 0  # Negative correlation second