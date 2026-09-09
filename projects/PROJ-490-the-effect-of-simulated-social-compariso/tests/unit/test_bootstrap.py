import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.bootstrap import (
    run_single_bootstrap_iteration,
    calculate_confidence_intervals,
    calculate_ci_width_variance,
    run_bootstrap_stability
)

@pytest.fixture
def sample_data():
    """Generate a small deterministic dataset for testing."""
    np.random.seed(42)
    n = 50
    data = {
        'post_self_esteem': np.random.normal(5, 1, n),
        'pre_self_esteem': np.random.normal(5, 1, n),
        'avatar_condition': np.random.choice([0, 1], n),
        'comparison_tendency': np.random.normal(0, 1, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def formula():
    return "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency"

def test_run_single_bootstrap_iteration(sample_data, formula):
    """Test that a single iteration returns a valid coefficient dictionary."""
    result = run_single_bootstrap_iteration(sample_data, formula, seed=100)
    assert result is not None
    assert 'Intercept' in result
    assert 'avatar_condition' in result
    assert isinstance(result['avatar_condition'], float)

def test_calculate_confidence_intervals(sample_data, formula):
    """Test CI calculation with a small set of bootstrap results."""
    # Generate 100 iterations manually for test
    results = []
    for i in range(100):
        r = run_single_bootstrap_iteration(sample_data, formula, seed=i)
        if r:
            results.append(r)
    
    lower, upper = calculate_confidence_intervals(results, 'avatar_condition')
    assert lower < upper
    assert not np.isnan(lower)
    assert not np.isnan(upper)

def test_calculate_ci_width_variance(sample_data, formula):
    """Test variance calculation logic."""
    results = []
    for i in range(200): # Ensure enough data
        r = run_single_bootstrap_iteration(sample_data, formula, seed=i)
        if r:
            results.append(r)
    
    variance = calculate_ci_width_variance(results, 'avatar_condition')
    assert isinstance(variance, float)
    assert variance >= 0

def test_run_bootstrap_stability_convergence(sample_data, formula):
    """
    Test that the stability loop runs and returns expected keys.
    Note: We use a very high threshold to ensure it stops early in testing.
    """
    # Use a high threshold to force early stop for testing speed
    result = run_bootstrap_stability(
        sample_data, 
        formula, 
        target_param='avatar_condition',
        max_iterations=100,
        variance_threshold=10.0 # Force early stop
    )
    
    assert 'iterations_performed' in result
    assert 'final_variance' in result
    assert 'stability_achieved' in result
    assert 'results' in result
    assert result['iterations_performed'] > 0
    assert result['stability_achieved'] == True # Because threshold was high

def test_run_bootstrap_stability_no_convergence(sample_data, formula):
    """
    Test behavior when stability is NOT achieved within max iterations.
    """
    result = run_bootstrap_stability(
        sample_data,
        formula,
        target_param='avatar_condition',
        max_iterations=20, # Low limit
        variance_threshold=0.0001 # Very strict
    )
    
    assert result['stability_achieved'] == False
    assert result['iterations_performed'] == 20
    assert result['final_variance'] > 0.0001
