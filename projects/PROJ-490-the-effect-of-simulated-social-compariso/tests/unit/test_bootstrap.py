import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.bootstrap import (
    calculate_ci_width_variance,
    run_single_bootstrap_iteration,
    calculate_confidence_intervals,
    run_bootstrap_stability
)
from data.config import get_config, reset_config

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "post_self_esteem": np.random.normal(50, 10, n),
        "pre_self_esteem": np.random.normal(48, 10, n),
        "avatar_condition": np.random.binomial(1, 0.5, n),
        "interaction_term": np.random.normal(0, 1, n)
    })
    return data

@pytest.fixture
def config():
    """Setup config for tests."""
    reset_config()
    cfg = get_config()
    cfg.seed = 42
    return cfg

def test_calculate_confidence_intervals():
    """Test CI calculation from bootstrap coefficients."""
    np.random.seed(42)
    coefficients = np.random.normal(0.2, 0.1, 1000).tolist()
    
    lower, upper = calculate_confidence_intervals(coefficients, ci_level=0.95)
    
    assert lower < upper
    assert len(coefficients) > 0
    assert isinstance(lower, float)
    assert isinstance(upper, float)

def test_calculate_ci_width_variance(sample_data, config):
    """Test CI width variance calculation (SC-004)."""
    # Use a small number of iterations for speed in tests
    results = calculate_ci_width_variance(
        coefficients=None,
        ci_level=0.95,
        n_iterations=50,  # Small number for test speed
        seed=42,
        data=sample_data
    )
    
    assert "ci_width_variance" in results
    assert "mean_ci_width" in results
    assert "ci_lower" in results
    assert "ci_upper" in results
    assert "flagged" in results
    assert "threshold" in results
    
    # Check that variance is a non-negative number
    assert results["ci_width_variance"] >= 0
    assert results["threshold"] == 0.01
    
    # The flagged field should be boolean
    assert isinstance(results["flagged"], bool)

def test_ci_width_variance_flagging(sample_data, config):
    """Test that CI width variance flagging works correctly."""
    # With stable data, variance should typically be < 0.01
    results = calculate_ci_width_variance(
        coefficients=None,
        ci_level=0.95,
        n_iterations=100,
        seed=42,
        data=sample_data
    )
    
    # The variance should be calculated
    assert results["ci_width_variance"] >= 0
    
    # Check that the flagging logic is correct
    expected_flagged = results["ci_width_variance"] >= 0.01
    assert results["flagged"] == expected_flagged

def test_run_bootstrap_stability(sample_data, config):
    """Test full bootstrap stability analysis."""
    results = run_bootstrap_stability(
        data=sample_data,
        n_iterations=50,  # Small number for test speed
        seed=42
    )
    
    assert "ci_width_variance" in results
    assert "mean_ci_width" in results
    assert "flagged" in results
    assert results["n_iterations"] == 50

def test_run_single_bootstrap_iteration(sample_data, config):
    """Test single bootstrap iteration."""
    rng = np.random.default_rng(42)
    
    coef, se = run_single_bootstrap_iteration(
        sample_data,
        "post_self_esteem",
        "pre_self_esteem",
        "avatar_condition",
        "interaction_term",
        rng
    )
    
    assert isinstance(coef, float)
    assert isinstance(se, float)
    assert se >= 0  # Standard error should be non-negative

def test_ci_width_variance_with_precomputed_coefficients(sample_data, config):
    """Test CI width variance with pre-computed coefficients."""
    # Generate some fake coefficients
    np.random.seed(42)
    coefficients = np.random.normal(0.2, 0.1, 1000).tolist()
    
    results = calculate_ci_width_variance(
        coefficients=coefficients,
        ci_level=0.95,
        n_iterations=100,
        seed=42
    )
    
    assert "ci_width_variance" in results
    assert results["ci_width_variance"] >= 0
    assert "flagged" in results

def test_ci_width_variance_stability_threshold():
    """Test that the stability threshold (0.01) is correctly applied."""
    # Create a scenario with high variance
    np.random.seed(42)
    # Generate coefficients with high variance
    high_var_coefs = np.random.normal(0.2, 0.5, 1000).tolist()
    
    results = calculate_ci_width_variance(
        coefficients=high_var_coefs,
        ci_level=0.95,
        n_iterations=100,
        seed=42
    )
    
    # With high variance coefficients, we expect higher CI width variance
    # This might or might not exceed 0.01 depending on the subsampling
    assert "ci_width_variance" in results
    assert results["threshold"] == 0.01
    assert isinstance(results["flagged"], bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
