"""
Unit tests for T035: Multiprocessing robustness checks.
"""
import pytest
import pandas as pd
import numpy as np
from robustness import _bootstrap_worker, run_bootstrap, run_alpha_sweep

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'IAT_D_score': np.random.randn(n),
        'news_exposure_z': np.random.randn(n),
        'political_ideology': np.random.randn(n),
        'age': np.random.randint(18, 80, n),
        'gender': np.random.choice([0, 1], n),
        'education': np.random.randint(1, 5, n)
    })

def test_bootstrap_worker_convergence(sample_data):
    """Test that the worker function returns valid results."""
    indices = np.random.choice(len(sample_data), size=len(sample_data), replace=True)
    args = (sample_data, indices, 42, "IAT_D_score ~ news_exposure_z * political_ideology", 0)
    
    result = _bootstrap_worker(args)
    
    assert 'coefficient' in result
    assert 'p_value' in result
    assert 'converged' in result
    assert isinstance(result['converged'], bool)

def test_run_bootstrap_small_sample(sample_data):
    """Test bootstrap with a small number of resamples."""
    # Use a very small number for unit test speed
    results, metrics = run_bootstrap(sample_data, formula="IAT_D_score ~ news_exposure_z * political_ideology")
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert 'mean_coefficient' in metrics
    assert 'convergence_pct' in metrics
    assert metrics['total_resamples'] == len(results)

def test_alpha_sweep(sample_data):
    """Test alpha sweep returns correct structure."""
    df = run_alpha_sweep(sample_data, formula="IAT_D_score ~ news_exposure_z * political_ideology")
    
    assert isinstance(df, pd.DataFrame)
    assert 'alpha_level' in df.columns
    assert 'significant' in df.columns
    assert len(df) == 3  # 0.01, 0.05, 0.10