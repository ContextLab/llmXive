"""
Unit tests for power analysis module.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stats.power import (
    simulate_correlation_data,
    calculate_spearman_correlation,
    t_test_for_correlation,
    run_monte_carlo_power_simulation,
    run_power_analysis
)

class TestPowerAnalysis:
    """Test cases for power analysis functions."""
    
    def test_simulate_correlation_data(self):
        """Test data simulation with known correlation."""
        n = 100
        rho = 0.5
        seed = 42
        
        x, y = simulate_correlation_data(n, rho, seed)
        
        assert len(x) == n
        assert len(y) == n
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
    
    def test_calculate_spearman_correlation(self):
        """Test Spearman correlation calculation."""
        # Perfect positive correlation
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r = calculate_spearman_correlation(x, y)
        assert abs(r - 1.0) < 1e-6
        
        # Perfect negative correlation
        y_neg = np.array([10, 8, 6, 4, 2])
        r_neg = calculate_spearman_correlation(x, y_neg)
        assert abs(r_neg - (-1.0)) < 1e-6
        
        # No correlation (random)
        np.random.seed(42)
        x_rand = np.random.randn(100)
        y_rand = np.random.randn(100)
        r_rand = calculate_spearman_correlation(x_rand, y_rand)
        assert abs(r_rand) < 0.3  # Should be close to 0
    
    def test_t_test_for_correlation(self):
        """Test t-test for correlation."""
        # High correlation should give low p-value
        r = 0.8
        n = 50
        p = t_test_for_correlation(r, n)
        assert p < 0.001
        
        # Zero correlation should give high p-value
        r_zero = 0.0
        p_zero = t_test_for_correlation(r_zero, n)
        assert p_zero == 1.0
    
    def test_monte_carlo_power_simulation(self):
        """Test Monte Carlo power simulation."""
        n_samples = 100
        target_rho = 0.5
        n_iterations = 100
        seed = 42
        
        results = run_monte_carlo_power_simulation(
            n_samples, target_rho, n_iterations, seed
        )
        
        assert "power" in results
        assert "significant_count" in results
        assert "total_iterations" in results
        assert results["total_iterations"] == n_iterations
        assert 0 <= results["power"] <= 1
    
    def test_run_power_analysis(self):
        """Test main power analysis function."""
        results = run_power_analysis(
            n_samples=100,
            target_rho=0.3,
            n_iterations=100,
            seed=42
        )
        
        assert "power_for_r03" in results
        assert "is_sufficient" in results
        assert "simulation_seed" in results
        assert results["simulation_seed"] == 42
        assert isinstance(results["is_sufficient"], bool)
    
    def test_power_threshold(self):
        """Test that power threshold is correctly evaluated."""
        # With large sample size and moderate effect, power should be high
        results_high = run_power_analysis(
            n_samples=200,
            target_rho=0.5,
            n_iterations=100,
            seed=42
        )
        assert results_high["is_sufficient"] == True
        
        # With small sample size, power might be low
        results_low = run_power_analysis(
            n_samples=30,
            target_rho=0.3,
            n_iterations=100,
            seed=42
        )
        # This might or might not be sufficient depending on the actual power
        assert isinstance(results_low["is_sufficient"], bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])