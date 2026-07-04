"""
Unit tests for the Bayesian Random Walk model (T021).
Tests model convergence and synthetic data edge cases.
"""
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Mock PyMC if not installed to allow test structure validation
# In a real run, PyMC must be installed.
try:
    import pymc as pm
    import arviz as az
    HAS_PMC = True
except ImportError:
    HAS_PMC = False
    pm = None
    az = None

from src.models.bayesian import fit_random_walk_model

@pytest.fixture
def synthetic_poll_data():
    """Generate synthetic poll data for testing."""
    np.random.seed(42)
    n_weeks = 10
    n_polls_per_week = 5
    
    weeks = []
    vote_shares = []
    sample_sizes = []
    rmse_vals = []
    
    # Simulate a random walk for truth
    true_theta = 50.0
    sigma_rw = 0.5
    
    for w in range(n_weeks):
        if w > 0:
            true_theta += np.random.normal(0, sigma_rw)
        
        for _ in range(n_polls_per_week):
            weeks.append(w)
            # Observation noise
            obs_noise = 2.0
            vote_shares.append(true_theta + np.random.normal(0, obs_noise))
            sample_sizes.append(1000) # Fixed sample size for simplicity
            rmse_vals.append(2.0)     # Fixed RMSE for simplicity

    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=len(weeks), freq='D'),
        'week_bin': weeks,
        'vote_share': vote_shares,
        'sample_size': sample_sizes,
        'historical_rmse': rmse_vals
    })
    return df

@pytest.mark.skipif(not HAS_PMC, reason="PyMC not installed")
def test_model_convergence(synthetic_poll_data):
    """Test that the model converges on synthetic data (R-hat <= 1.05)."""
    # Use fewer draws for speed in tests
    idata, forecasts_df = fit_random_walk_model(
        synthetic_poll_data,
        election_outcomes=pd.DataFrame(),
        tune=500,
        draws=500,
        chains=2,
        random_seed=42
    )
    
    # Check convergence
    r_hat = az.rhat(idata)
    # Check max R-hat across all variables
    max_rhat = 0.0
    for var in r_hat.data_vars:
        val = r_hat[var].values
        if np.isscalar(val):
            max_rhat = max(max_rhat, val)
        else:
            max_rhat = max(max_rhat, np.max(val))
    
    assert max_rhat <= 1.05, f"Model did not converge: Max R-hat = {max_rhat}"
    assert len(forecasts_df) == len(synthetic_poll_data['week_bin'].unique())
    assert 'bayesian_forecast' in forecasts_df.columns

@pytest.mark.skipif(not HAS_PMC, reason="PyMC not installed")
def test_single_week_edge_case(synthetic_poll_data):
    """Test behavior with minimal data (single week)."""
    # Filter to single week
    single_week_data = synthetic_poll_data[synthetic_poll_data['week_bin'] == 0].copy()
    
    # This might be too little data for a proper RW, but should not crash
    # We expect it to run, though convergence might be tricky with very few points
    # For the test, we just ensure it doesn't raise an exception immediately
    # We might need to adjust parameters for such small data
    try:
        idata, forecasts_df = fit_random_walk_model(
            single_week_data,
            election_outcomes=pd.DataFrame(),
            tune=200,
            draws=200,
            chains=1,
            random_seed=42
        )
        assert len(forecasts_df) == 1
    except RuntimeError as e:
        # If it fails due to convergence on such small data, that's acceptable behavior
        # The important thing is the model structure is correct
        if "did not converge" in str(e):
            pass # Acceptable
        else:
            raise

def test_missing_pymc():
    """Test that the function raises RuntimeError if PyMC is missing."""
    # This test is only relevant if PyMC is actually missing
    if HAS_PMC:
        pytest.skip("PyMC is installed, skipping missing dependency test")
    
    df = pd.DataFrame({
        'week_bin': [0, 1],
        'vote_share': [50, 51],
        'sample_size': [100, 100],
        'historical_rmse': [2.0, 2.0]
    })
    
    with pytest.raises(RuntimeError, match="PyMC is not installed"):
        fit_random_walk_model(df, pd.DataFrame())
