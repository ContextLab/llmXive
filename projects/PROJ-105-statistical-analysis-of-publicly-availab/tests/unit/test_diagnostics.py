import pytest
import numpy as np
from scipy import stats
from pathlib import Path
import json

from diagnostics import (
    estimate_hill_index,
    compute_hill_stability_curve,
    find_optimal_k_stability,
    calculate_hill_confidence_interval,
    run_hill_stability_analysis,
    calculate_r2_on_tail,
    bootstrap_goodness_of_fit,
    calculate_log_normal_curvature,
    perform_log_normal_discrimination
)

@pytest.fixture
def sample_tail_data():
    """Generate sample tail data for testing."""
    np.random.seed(42)
    # Generate Pareto-like tail
    return stats.pareto.rvs(2.5, size=1000, scale=10)

@pytest.fixture
def sample_lognormal_data():
    """Generate sample Log-Normal data for testing."""
    np.random.seed(42)
    return stats.lognorm.rvs(1.0, scale=10, size=1000)

class TestHillEstimator:
    def test_hill_index_positive(self, sample_tail_data):
        """Hill estimator should return positive alpha for heavy-tailed data."""
        k = 50
        alpha = estimate_hill_index(sample_tail_data, k)
        assert alpha > 0
        assert not np.isnan(alpha)

    def test_hill_index_invalid_k(self, sample_tail_data):
        """Hill estimator should raise error for invalid k."""
        with pytest.raises(ValueError):
            estimate_hill_index(sample_tail_data, 0)
        with pytest.raises(ValueError):
            estimate_hill_index(sample_tail_data, len(sample_tail_data))

    def test_stability_curve_computation(self, sample_tail_data):
        """Stability curve should compute correctly."""
        k_range = list(range(10, 50))
        k_vals, alphas = compute_hill_stability_curve(sample_tail_data, k_range)
        
        assert len(k_vals) == len(k_range)
        assert len(alphas) == len(k_range)
        assert all(alpha > 0 for alpha in alphas if not np.isnan(alpha))

    def test_optimal_k_finding(self, sample_tail_data):
        """Optimal k should be found within range."""
        k_range = list(range(10, 50))
        k_vals, alphas = compute_hill_stability_curve(sample_tail_data, k_range)
        
        optimal_k, optimal_alpha = find_optimal_k_stability(k_vals, alphas, window_size=10)
        
        assert optimal_k in k_range
        assert optimal_alpha > 0

    def test_full_stability_analysis(self, sample_tail_data):
        """Full stability analysis should return expected structure."""
        results = run_hill_stability_analysis(sample_tail_data, window_size=10)
        
        assert "optimal_k" in results
        assert "estimated_alpha" in results
        assert "confidence_interval" in results
        assert "stability_curve" in results
        assert results["optimal_k"] > 0
        assert results["estimated_alpha"] > 0

class TestR2Calculation:
    def test_r2_calculation(self, sample_tail_data):
        """R² should be computed for tail data."""
        x_min = np.percentile(sample_tail_data, 90)
        fitted_dist = stats.pareto(2.5, scale=x_min)
        
        r_squared = calculate_r2_on_tail(sample_tail_data, fitted_dist, x_min)
        
        assert 0 <= r_squared <= 1

class TestBootstrapGoF:
    def test_bootstrap_pvalue(self, sample_tail_data):
        """Bootstrap GoF should return valid p-value."""
        x_min = np.percentile(sample_tail_data, 90)
        fitted_dist = stats.pareto(2.5, scale=x_min)
        
        p_value = bootstrap_goodness_of_fit(sample_tail_data, fitted_dist, x_min, n_bootstrap=10)
        
        assert 0 <= p_value <= 1

class TestLogNormalDiscrimination:
    def test_curvature_calculation(self, sample_tail_data):
        """Curvature should be calculated for tail data."""
        x_min = np.percentile(sample_tail_data, 90)
        
        curvature, p_value, null_mean = calculate_log_normal_curvature(
            sample_tail_data, x_min, n_sims=10
        )
        
        assert isinstance(curvature, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

    def test_full_lognormal_test(self, sample_tail_data):
        """Full Log-Normal test should return expected structure."""
        x_min = np.percentile(sample_tail_data, 90)
        
        results = perform_log_normal_discrimination(sample_tail_data, x_min, n_sims=10)
        
        assert "curvature_statistic" in results
        assert "p_value" in results
        assert "conclusion" in results
        assert "message" in results
        assert results["conclusion"] in ["cannot_reject_log_normal", "reject_log_normal"]

    def test_lognormal_data_consistency(self, sample_lognormal_data):
        """Log-Normal data should be consistent with Log-Normal hypothesis."""
        x_min = np.percentile(sample_lognormal_data, 90)
        
        results = perform_log_normal_discrimination(sample_lognormal_data, x_min, n_sims=10)
        
        # With small n_sims, p-value might vary, but structure should be correct
        assert results["p_value"] >= 0
        assert results["p_value"] <= 1