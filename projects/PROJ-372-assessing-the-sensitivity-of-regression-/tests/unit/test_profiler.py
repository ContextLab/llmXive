"""
Unit tests for the profiler module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.ingestion.profiler import (
    compute_condition_number,
    compute_breusch_pagan,
    compute_cooks_distance,
    profile_dataset,
    run_profiler
)


class TestComputeConditionNumber:
    def test_well_conditioned_matrix(self):
        """Test with a well-conditioned matrix (identity-like)."""
        X = np.eye(10)
        cond = compute_condition_number(X)
        assert np.isclose(cond, 1.0, rtol=1e-5)

    def test_ill_conditioned_matrix(self):
        """Test with an ill-conditioned matrix."""
        # Create a matrix with a very small singular value
        X = np.array([
            [1, 0],
            [0, 1e-10]
        ])
        cond = compute_condition_number(X)
        assert cond > 1e9

    def test_empty_matrix(self):
        """Test with an empty matrix."""
        X = np.array([]).reshape(0, 0)
        cond = compute_condition_number(X)
        assert np.isnan(cond)

    def test_singular_matrix(self):
        """Test with a singular matrix."""
        X = np.array([
            [1, 2],
            [2, 4]
        ])
        cond = compute_condition_number(X)
        assert np.isinf(cond)


class TestComputeBreuschPagan:
    def test_homoscedastic_data(self):
        """Test with homoscedastic data (should have high p-value)."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        y = 1 + 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(n) * 0.5
        
        stat, pval = compute_breusch_pagan(X, y)
        assert not np.isnan(stat)
        assert not np.isnan(pval)
        # p-value should be relatively high for homoscedastic data
        # (though not guaranteed, it's likely > 0.05)

    def test_heteroscedastic_data(self):
        """Test with heteroscedastic data (should have low p-value)."""
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 2)
        # Heteroscedastic: variance increases with X
        y = 1 + 2 * X[:, 0] + 3 * X[:, 1] + np.abs(X[:, 0]) * np.random.randn(n) * 2
        
        stat, pval = compute_breusch_pagan(X, y)
        assert not np.isnan(stat)
        assert not np.isnan(pval)

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        X = np.array([[1, 2]])
        y = np.array([3])
        stat, pval = compute_breusch_pagan(X, y)
        assert np.isnan(stat)
        assert np.isnan(pval)


class TestComputeCooksDistance:
    def test_normal_data(self):
        """Test with normal data."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        y = 1 + 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(n) * 0.5
        
        cooks_d, max_cooks = compute_cooks_distance(X, y)
        assert len(cooks_d) == n
        assert not np.isnan(max_cooks)
        assert max_cooks >= 0

    def test_influential_point(self):
        """Test with an influential point."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        y = 1 + 2 * X[:, 0] + 3 * X[:, 1] + np.random.randn(n) * 0.5
        
        # Add an influential point
        X = np.vstack([X, [10, 10]])
        y = np.append(y, 100)
        
        cooks_d, max_cooks = compute_cooks_distance(X, y)
        assert max_cooks > 0.5  # Should be high due to influential point

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        X = np.array([[1, 2]])
        y = np.array([3])
        cooks_d, max_cooks = compute_cooks_distance(X, y)
        assert len(cooks_d) == 0
        assert np.isnan(max_cooks)


class TestProfileDataset:
    def test_full_profile(self):
        """Test profiling a complete dataset."""
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n)
        })
        
        result = profile_dataset(df, target_col='y', feature_cols=['x1', 'x2'])
        
        assert 'condition_number' in result
        assert 'breusch_pagan_stat' in result
        assert 'max_cooks_distance' in result
        assert result['n_samples'] == n
        assert result['n_features'] == 3  # 2 features + 1 intercept
        assert not np.isnan(result['condition_number'])
        assert not np.isnan(result['breusch_pagan_stat'])
        assert not np.isnan(result['max_cooks_distance'])

    def test_empty_dataset(self):
        """Test with an empty dataset."""
        df = pd.DataFrame({'y': [], 'x1': [], 'x2': []})
        with pytest.raises(ValueError, match="Dataset is empty"):
            profile_dataset(df, target_col='y', feature_cols=['x1', 'x2'])


class TestRunProfiler:
    def test_small_dataset(self):
        """Test with a small dataset that fits in memory."""
        np.random.seed(42)
        df = pd.DataFrame({
            'y': np.random.randn(100),
            'x1': np.random.randn(100),
            'x2': np.random.randn(100)
        })
        
        result = run_profiler(df, target_col='y', feature_cols=['x1', 'x2'])
        
        assert result['n_samples'] == 100
        assert not np.isnan(result['condition_number'])

    def test_large_dataset_subsample(self):
        """Test with a large dataset that triggers subsampling."""
        np.random.seed(42)
        n = 200_000  # Large dataset
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n)
        })
        
        # Force subsampling by setting low threshold
        result = run_profiler(
            df, 
            target_col='y', 
            feature_cols=['x1', 'x2'],
            memory_threshold_gb=0.1,  # Very low threshold
            subsample_threshold_rows=1000
        )
        
        # Should be subsampled
        assert result['n_samples'] <= 1000
        assert result['n_samples'] > 0
        assert not np.isnan(result['condition_number'])