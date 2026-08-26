"""
Unit tests for the subsampling logic in profiler.py (Task T016).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from src.ingestion.profiler import profile_dataset, _compute_ols_stats
from src.models.data_models import ViolationSeverity


def test_subsample_threshold_not_exceeded():
    """Test that small datasets are processed fully (not subsampled)."""
    n = 5000
    df = pd.DataFrame({
        'y': np.random.randn(n),
        'x1': np.random.randn(n),
        'x2': np.random.randn(n)
    })
    
    profile = profile_dataset(df, 'y', ['x1', 'x2'], subsample_threshold=10000)
    
    assert profile.is_subsampled is False
    assert profile.n_samples == n


def test_subsample_threshold_exceeded():
    """Test that large datasets trigger subsampling logic."""
    n = 150000
    df = pd.DataFrame({
        'y': np.random.randn(n),
        'x1': np.random.randn(n),
        'x2': np.random.randn(n)
    })
    
    profile = profile_dataset(df, 'y', ['x1', 'x2'], subsample_threshold=100000)
    
    assert profile.is_subsampled is True
    # The n_samples in the profile should reflect the subsample size used
    assert profile.n_samples <= 110000 # 100k + 10% buffer


def test_stability_check_passes():
    """
    Test that if BP stats are stable (<5% dev), the smaller sample result is used.
    """
    # We mock _compute_ols_stats to return specific values
    # Sample 1 (100k): BP = 10.0
    # Sample 2 (110k): BP = 10.2 (2% deviation) -> Should pass, use Sample 1
    
    with patch('src.ingestion.profiler._compute_ols_stats') as mock_stats:
        # Mock return values: first call (sample 1), second call (sample 2)
        mock_stats.side_effect = [
            {"condition_number": 10.0, "bp_stat": 10.0, "bp_pvalue": 0.5, "max_cooks_distance": 0.1, "singularity_detected": False, "n_samples": 100000},
            {"condition_number": 10.1, "bp_stat": 10.2, "bp_pvalue": 0.49, "max_cooks_distance": 0.11, "singularity_detected": False, "n_samples": 110000}
        ]
        
        n = 200000
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n)
        })
        
        profile = profile_dataset(df, 'y', ['x1', 'x2'], subsample_threshold=100000)
        
        # Should have used the first sample's stats because deviation < 5%
        assert profile.breusch_pagan_stat == 10.0
        assert profile.n_samples == 100000
        assert mock_stats.call_count == 2


def test_stability_check_fails_fallback_larger():
    """
    Test that if BP stats are unstable (>5% dev), the larger sample result is used.
    """
    # Sample 1 (100k): BP = 10.0
    # Sample 2 (110k): BP = 12.0 (20% deviation) -> Should fail, use Sample 2
    
    with patch('src.ingestion.profiler._compute_ols_stats') as mock_stats:
        mock_stats.side_effect = [
            {"condition_number": 10.0, "bp_stat": 10.0, "bp_pvalue": 0.5, "max_cooks_distance": 0.1, "singularity_detected": False, "n_samples": 100000},
            {"condition_number": 10.1, "bp_stat": 12.0, "bp_pvalue": 0.49, "max_cooks_distance": 0.11, "singularity_detected": False, "n_samples": 110000}
        ]
        
        n = 200000
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': np.random.randn(n),
            'x2': np.random.randn(n)
        })
        
        profile = profile_dataset(df, 'y', ['x1', 'x2'], subsample_threshold=100000)
        
        # Should have used the second sample's stats
        assert profile.breusch_pagan_stat == 12.0
        assert profile.n_samples == 110000
        assert mock_stats.call_count == 2