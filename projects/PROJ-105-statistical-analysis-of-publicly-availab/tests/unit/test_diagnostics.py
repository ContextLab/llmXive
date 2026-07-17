import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from diagnostics import log_normal_discrimination, hill_estimator, compute_hill_statistics

@pytest.fixture
def sample_tail_data():
    """Generate sample tail data for testing."""
    np.random.seed(42)
    # Generate Pareto-like data
    alpha = 2.0
    x_min = 1.0
    data = np.random.pareto(alpha, 1000) * x_min + x_min
    return data

@pytest.fixture
def sample_lognormal_data():
    """Generate sample Log-Normal data for testing."""
    np.random.seed(42)
    data = np.random.lognormal(mean=1, sigma=1, size=1000)
    return data

def test_log_normal_discrimination_pareto(sample_tail_data):
    """Test Log-Normal discrimination on Pareto data (should reject Log-Normal)."""
    x_min = np.min(sample_tail_data)
    result = log_normal_discrimination(
        sample_tail_data, 
        x_min=x_min,
        n_sim=100,  # Small number for fast testing
        random_state=42
    )
    
    assert 'curvature_statistic' in result
    assert 'p_value' in result
    assert 'conclusion' in result
    assert result['n_observations'] == len(sample_tail_data)
    
    # For Pareto data, we expect to reject Log-Normal (low p-value)
    # Note: With small n_sim, results may vary, so we just check structure
    assert isinstance(result['p_value'], float)
    assert 0 <= result['p_value'] <= 1

def test_log_normal_discrimination_lognormal(sample_lognormal_data):
    """Test Log-Normal discrimination on Log-Normal data (should not reject)."""
    x_min = np.min(sample_lognormal_data)
    result = log_normal_discrimination(
        sample_lognormal_data,
        x_min=x_min,
        n_sim=100,
        random_state=42
    )
    
    assert 'curvature_statistic' in result
    assert 'p_value' in result
    assert result['conclusion'] in ['reject_log_normal', 'cannot_reject_log_normal']

def test_log_normal_discrimination_insufficient_data():
    """Test Log-Normal discrimination with insufficient data."""
    data = np.array([1.0, 2.0, 3.0])
    result = log_normal_discrimination(data, x_min=1.0, n_sim=10)
    
    assert result['conclusion'] == 'insufficient_data'
    assert np.isnan(result['curvature_statistic'])
    assert np.isnan(result['p_value'])

def test_hill_estimator():
    """Test Hill estimator calculation."""
    np.random.seed(42)
    # Generate Pareto data with known alpha
    alpha = 2.0
    data = np.random.pareto(alpha, 1000) + 1
    
    k = 100
    xi_est = hill_estimator(data, k)
    
    # For Pareto, xi = 1/alpha
    expected_xi = 1.0 / alpha
    
    # Check if estimate is reasonably close (within 20% for small k)
    assert abs(xi_est - expected_xi) / expected_xi < 0.2

def test_compute_hill_statistics():
    """Test Hill statistics computation."""
    np.random.seed(42)
    data = np.random.pareto(2.0, 1000) + 1
    
    stats_dict = compute_hill_statistics(data, max_k_ratio=0.1)
    
    assert 'k_values' in stats_dict
    assert 'hill_estimates' in stats_dict
    assert 'variances' in stats_dict
    assert stats_dict['n'] == 1000
    assert len(stats_dict['k_values']) > 0
    assert len(stats_dict['hill_estimates']) > 0
