import pytest
import numpy as np
from scipy import stats
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    fit_distribution,
    fit_all_base_distributions,
    fit_pareto_tail,
    estimate_x_min_ks,
    calculate_tail_metrics,
    perform_vuong_test,
    compare_component_distributions,
    ConvergenceError
)

@pytest.fixture
def sample_delay_data():
    """Generate sample delay data for testing."""
    np.random.seed(42)
    # Simulate a mix of short and long delays
    short_delays = np.random.exponential(scale=30, size=800)
    long_delays = np.random.pareto(a=1.5, size=200) * 60  # Scale to minutes
    data = np.concatenate([short_delays, long_delays])
    data = np.maximum(data, 0)  # Ensure non-negative
    return data

@pytest.fixture
def component_data():
    """Generate sample component delay data."""
    np.random.seed(42)
    arr_delay = np.random.exponential(scale=20, size=500)
    dep_delay = np.random.exponential(scale=25, size=500)
    total_delay = arr_delay + dep_delay
    return total_delay, arr_delay, dep_delay

def test_fit_distribution_convergence(sample_delay_data):
    """Test that fit_distribution converges for common distributions."""
    distributions = ['expon', 'gamma', 'lognorm', 'weibull_min']
    
    for dist_name in distributions:
        frozen_dist, params = fit_distribution(sample_delay_data, dist_name)
        assert frozen_dist is not None
        assert len(params) > 0
        assert all(not np.isnan(p) and not np.isinf(p) for p in params if p != 0)

def test_fit_distribution_pareto_tail(sample_delay_data):
    """Test Pareto fitting on tail data."""
    x_min = np.percentile(sample_delay_data, 80)
    frozen_dist, params = fit_pareto_tail(sample_delay_data, x_min)
    
    assert frozen_dist is not None
    assert 'b' in params
    assert params['b'] > 0
    assert params['x_min'] == x_min

def test_estimate_x_min_ks(sample_delay_data):
    """Test x_min estimation via KS minimization."""
    x_min = estimate_x_min_ks(sample_delay_data, grid_points=20)
    
    assert x_min > 0
    assert x_min < np.max(sample_delay_data)

def test_calculate_tail_metrics(sample_delay_data):
    """Test calculation of tail metrics."""
    x_min = estimate_x_min_ks(sample_delay_data, grid_points=20)
    fitted_results = fit_all_base_distributions_tail(sample_delay_data, x_min)
    
    metrics = calculate_tail_metrics(sample_delay_data, fitted_results, x_min)
    
    assert len(metrics) > 0
    for dist_name, metric in metrics.items():
        assert 'aic' in metric
        assert 'bic' in metric
        assert 'ks_statistic' in metric
        assert 'ks_p_value' in metric

def test_perform_vuong_test(sample_delay_data):
    """Test Vuong test implementation."""
    x_min = estimate_x_min_ks(sample_delay_data, grid_points=20)
    fitted_results = fit_all_base_distributions_tail(sample_delay_data, x_min)
    
    if len(fitted_results) >= 2:
        dist_names = list(fitted_results.keys())
        model1 = fitted_results[dist_names[0]][0]
        model2 = fitted_results[dist_names[1]][0]
        
        results = perform_vuong_test(sample_delay_data, model1, model2, x_min)
        
        assert 'vuong_z' in results
        assert 'p_value' in results
        assert results['p_value'] >= 0
        assert results['p_value'] <= 1

def test_compare_component_distributions(component_data):
    """Test component distribution comparison."""
    total_delay, arr_delay, dep_delay = component_data
    
    results = compare_component_distributions(total_delay, arr_delay, dep_delay)
    
    assert 'sample_sizes' in results
    assert 'descriptive_statistics' in results
    assert 'ks_tests' in results
    assert 'correlations' in results
    
    assert results['sample_sizes']['total_delay'] == len(total_delay)
    assert results['sample_sizes']['arr_delay'] == len(arr_delay)
    assert results['sample_sizes']['dep_delay'] == len(dep_delay)

def test_compare_component_distributions_with_negatives():
    """Test component comparison handles negative values correctly."""
    np.random.seed(42)
    arr_delay = np.random.normal(loc=10, scale=20, size=500)  # Some negative
    dep_delay = np.random.normal(loc=15, scale=25, size=500)
    total_delay = arr_delay + dep_delay
    
    # Should not raise error, just filter negatives
    results = compare_component_distributions(total_delay, arr_delay, dep_delay)
    
    assert results['sample_sizes']['total_delay'] < 500  # Some filtered out
    assert results['sample_sizes']['total_delay'] > 0

def test_fit_distribution_non_convergence():
    """Test that non-convergence raises ConvergenceError."""
    # Use pathological data that won't fit well
    pathological_data = np.array([0.0] * 100)  # All zeros
    
    with pytest.raises(ConvergenceError):
        fit_distribution(pathological_data, 'gamma')