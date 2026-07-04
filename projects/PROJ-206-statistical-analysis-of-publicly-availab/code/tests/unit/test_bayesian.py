"""
Unit tests for Bayesian Random Walk model (T021).

Tests:
- Synthetic data generation and model fitting
- Convergence checks (R-hat)
- Edge cases (single observation, zero variance)
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.bayesian import (
    load_processed_poll_data,
    prepare_random_walk_data,
    run_random_walk_model,
    check_convergence,
    generate_forecasts
)

@pytest.fixture
def synthetic_data():
    """Generate synthetic data for testing."""
    np.random.seed(42)
    n_weeks = 20
    weeks = np.arange(n_weeks)
    
    # Random walk latent state
    theta = np.zeros(n_weeks)
    sigma_rw = 0.05
    for t in range(1, n_weeks):
        theta[t] = theta[t-1] + np.random.normal(0, sigma_rw)
    
    # Add initial drift
    theta += 0.5
    
    # Observation noise
    sigma_obs = np.full(n_weeks, 0.03)
    y = theta + np.random.normal(0, sigma_obs)
    
    return y, sigma_obs, n_weeks

def test_prepare_random_walk_data():
    """Test data preparation function."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'pollster', 'vote_share', 'sample_size', 'historical_rmse'])
        
        dates = pd.date_range('2020-01-01', periods=10, freq='W')
        for i, date in enumerate(dates):
            writer.writerow([
                date.strftime('%Y-%m-%d'),
                f'Pollster_{i}',
                0.5 + 0.01 * i,
                1000,
                0.03
            ])
        temp_path = Path(f.name)
    
    try:
        df = pd.read_csv(temp_path)
        df['date'] = pd.to_datetime(df['date'])
        
        y, sigma_obs, weeks, n_weeks = prepare_random_walk_data(df)
        
        assert len(y) == n_weeks
        assert len(sigma_obs) == n_weeks
        assert len(weeks) == n_weeks
        assert n_weeks == 10
        assert all(sigma_obs > 0)
    finally:
        temp_path.unlink()

def test_run_random_walk_model_synthetic(synthetic_data):
    """Test model fitting on synthetic data."""
    y, sigma_obs, n_weeks = synthetic_data
    
    # Run with minimal tuning for speed in tests
    trace = run_random_walk_model(
        y, sigma_obs, n_weeks,
        tune=100,
        draws=100,
        chains=1,
        random_seed=42
    )
    
    assert isinstance(trace, az.InferenceData)
    assert 'posterior' in trace
    assert 'theta' in trace.posterior
    
    # Check shape
    theta_shape = trace.posterior['theta'].shape
    assert theta_shape[-1] == n_weeks

def test_check_convergence_pass(synthetic_data):
    """Test convergence check on converged model."""
    y, sigma_obs, n_weeks = synthetic_data
    trace = run_random_walk_model(
        y, sigma_obs, n_weeks,
        tune=100,
        draws=100,
        chains=1,
        random_seed=42
    )
    
    # Should pass
    assert check_convergence(trace, rhat_threshold=1.1)

def test_generate_forecasts(synthetic_data):
    """Test forecast generation."""
    y, sigma_obs, n_weeks = synthetic_data
    trace = run_random_walk_model(
        y, sigma_obs, n_weeks,
        tune=100,
        draws=100,
        chains=1,
        random_seed=42
    )
    
    df_forecasts = generate_forecasts(trace, n_weeks)
    
    assert 'week_idx' in df_forecasts.columns
    assert 'bayesian_forecast' in df_forecasts.columns
    assert 'ci_lower_95' in df_forecasts.columns
    assert 'ci_upper_95' in df_forecasts.columns
    assert len(df_forecasts) == n_weeks
    
    # Check CI validity
    assert all(df_forecasts['ci_lower_95'] <= df_forecasts['bayesian_forecast'])
    assert all(df_forecasts['bayesian_forecast'] <= df_forecasts['ci_upper_95'])

def test_single_observation():
    """Test edge case with single observation."""
    y = np.array([0.5])
    sigma_obs = np.array([0.03])
    n_weeks = 1
    
    trace = run_random_walk_model(
        y, sigma_obs, n_weeks,
        tune=50,
        draws=50,
        chains=1,
        random_seed=42
    )
    
    assert 'theta' in trace.posterior

def test_zero_observation_variance():
    """Test handling of near-zero observation variance."""
    y = np.array([0.5, 0.51, 0.52])
    sigma_obs = np.array([1e-5, 1e-5, 1e-5]) # Very small but not zero
    n_weeks = 3
    
    # Should not crash
    trace = run_random_walk_model(
        y, sigma_obs, n_weeks,
        tune=50,
        draws=50,
        chains=1,
        random_seed=42
    )
    
    assert 'theta' in trace.posterior

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
