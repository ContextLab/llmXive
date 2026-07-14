"""
Integration test for adaptive replication loop termination (T017).

Verifies that the simulation engine's adaptive replication loop:
1. Starts with the minimum number of replicates (1000)
2. Calculates Clopper-Pearson exact intervals correctly
3. Terminates when CI width <= 0.01
4. Terminates when max replicates cap is reached
5. Correctly handles edge cases (p=0, p=1)

This test uses a mock scenario with known outcomes to verify loop behavior
without running the full simulation cost.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from typing import List, Tuple, Dict, Any

# Import the simulation engine components
# Note: We import the module but mock the heavy computation parts
# to focus on the adaptive loop logic
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from config import get_simulation_grid, get_test_grid
from data_generator import generate_normal

# We will implement a minimal simulation loop here for testing purposes
# since the full simulation_engine.py is not yet implemented (T018)
# This allows us to test the adaptive logic independently

def clopper_pearson_interval(successes: int, trials: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate Clopper-Pearson exact confidence interval for a binomial proportion.
    
    Args:
        successes: Number of successes
        trials: Total number of trials
        alpha: Significance level (default 0.05 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    from scipy.stats import beta
    
    if trials == 0:
        return (0.0, 0.0)
    
    if successes == 0:
        lower = 0.0
    else:
        lower = beta.ppf(alpha / 2, successes, trials - successes + 1)
    
    if successes == trials:
        upper = 1.0
    else:
        upper = beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    
    return (lower, upper)

def simulate_single_replicate_null_true() -> bool:
    """
    Simulate a single replicate where null hypothesis is true.
    Returns True if we reject (Type I error), False otherwise.
    
    For testing purposes, we simulate a scenario where the rejection
    probability is known (e.g., 0.05 for Type I error under null).
    """
    # In a real scenario, this would run the actual statistical test
    # For this test, we use a controlled random process with known probability
    return np.random.random() < 0.05

def run_adaptive_simulation(
    scenario: Dict[str, Any],
    min_replicates: int = 1000,
    max_replicates: int = 5000,
    ci_width_target: float = 0.01,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run adaptive Monte Carlo simulation with Clopper-Pearson intervals.
    
    Args:
        scenario: Simulation scenario parameters
        min_replicates: Minimum number of replicates
        max_replicates: Maximum number of replicates
        ci_width_target: Target CI width for termination
        alpha: Significance level for CI calculation
        
    Returns:
        Dictionary with simulation results and metadata
    """
    successes = 0
    total_replicates = 0
    ci_widths = []
    
    while total_replicates < max_replicates:
        # Run a batch of replicates (or one at a time for precision)
        batch_size = min(100, max_replicates - total_replicates)
        if total_replicates + batch_size < min_replicates:
            batch_size = min_replicates - total_replicates
        
        for _ in range(batch_size):
            if simulate_single_replicate_null_true():
                successes += 1
            total_replicates += 1
        
        # Calculate CI if we have enough replicates
        if total_replicates >= min_replicates:
            lower, upper = clopper_pearson_interval(successes, total_replicates, alpha)
            ci_width = upper - lower
            ci_widths.append(ci_width)
            
            # Check termination condition
            if ci_width <= ci_width_target:
                break
    
    observed_rate = successes / total_replicates if total_replicates > 0 else 0.0
    lower, upper = clopper_pearson_interval(successes, total_replicates, alpha)
    
    return {
        'scenario': scenario,
        'total_replicates': total_replicates,
        'successes': successes,
        'observed_rate': observed_rate,
        'ci_lower': lower,
        'ci_upper': upper,
        'ci_width': upper - lower,
        'ci_widths_history': ci_widths,
        'terminated_by_ci': ci_widths and ci_widths[-1] <= ci_width_target,
        'terminated_by_max': total_replicates >= max_replicates
    }

class TestAdaptiveReplicationLoop:
    """Integration tests for adaptive replication loop termination."""
    
    def test_loop_starts_with_minimum_replicates(self):
        """Test that the loop runs at least min_replicates before checking termination."""
        scenario = {'n': 50, 'distribution': 'normal', 'test': 't-test', 'hypothesis': 'null_true'}
        result = run_adaptive_simulation(scenario, min_replicates=1000, max_replicates=5000)
        
        assert result['total_replicates'] >= 1000, \
            f"Loop should start with at least 1000 replicates, got {result['total_replicates']}"
    
    def test_loop_terminates_when_ci_width_target_reached(self):
        """Test that loop terminates when CI width <= target."""
        scenario = {'n': 50, 'distribution': 'normal', 'test': 't-test', 'hypothesis': 'null_true'}
        
        # With a large number of replicates, CI width should eventually become small
        result = run_adaptive_simulation(
            scenario, 
            min_replicates=1000, 
            max_replicates=10000,
            ci_width_target=0.01
        )
        
        # The loop should have terminated either by CI width or max replicates
        assert result['total_replicates'] <= 10000, \
            f"Loop should not exceed max_replicates, got {result['total_replicates']}"
        
        if result['terminated_by_ci']:
            assert result['ci_width'] <= 0.01, \
                f"CI width should be <= 0.01 when terminated by CI, got {result['ci_width']}"
    
    def test_loop_terminates_at_max_replicates_cap(self):
        """Test that loop terminates when max_replicates is reached."""
        scenario = {'n': 50, 'distribution': 'normal', 'test': 't-test', 'hypothesis': 'null_true'}
        
        # Set a very small max_replicates to force termination by cap
        result = run_adaptive_simulation(
            scenario,
            min_replicates=100,
            max_replicates=200,
            ci_width_target=0.0001  # Very small target to prevent early termination
        )
        
        assert result['total_replicates'] == 200, \
            f"Loop should terminate at max_replicates=200, got {result['total_replicates']}"
        assert result['terminated_by_max'], \
            "Loop should indicate termination by max_replicates"
    
    def test_clopper_pearson_interval_calculation(self):
        """Test Clopper-Pearson interval calculation with known values."""
        # Test case: 50 successes out of 1000 trials, alpha=0.05
        # Expected: approximately 0.035 to 0.065
        lower, upper = clopper_pearson_interval(50, 1000, 0.05)
        
        assert 0.03 <= lower <= 0.04, f"Lower bound should be around 0.035, got {lower}"
        assert 0.06 <= upper <= 0.07, f"Upper bound should be around 0.065, got {upper}"
        
        # Test edge case: 0 successes
        lower, upper = clopper_pearson_interval(0, 1000, 0.05)
        assert lower == 0.0, f"Lower bound should be 0.0 for 0 successes, got {lower}"
        
        # Test edge case: all successes
        lower, upper = clopper_pearson_interval(1000, 1000, 0.05)
        assert upper == 1.0, f"Upper bound should be 1.0 for all successes, got {upper}"
    
    def test_adaptive_loop_convergence_behavior(self):
        """Test that CI width decreases as replicates increase."""
        scenario = {'n': 50, 'distribution': 'normal', 'test': 't-test', 'hypothesis': 'null_true'}
        
        # Run with a fixed seed for reproducibility
        np.random.seed(42)
        result = run_adaptive_simulation(
            scenario,
            min_replicates=1000,
            max_replicates=5000,
            ci_width_target=0.02  # Larger target to ensure termination
        )
        
        # CI widths should generally decrease (with some noise)
        ci_widths = result['ci_widths_history']
        if len(ci_widths) > 1:
            # Check that the final CI width is smaller than the initial
            # (allowing for some noise in the middle)
            assert ci_widths[-1] <= ci_widths[0] * 1.1, \
                f"Final CI width {ci_widths[-1]} should be <= initial {ci_widths[0]} (with tolerance)"
    
    def test_type_i_error_rate_stability(self):
        """Test that observed Type I error rate is stable and close to alpha."""
        scenario = {'n': 50, 'distribution': 'normal', 'test': 't-test', 'hypothesis': 'null_true'}
        
        np.random.seed(123)
        result = run_adaptive_simulation(
            scenario,
            min_replicates=2000,
            max_replicates=10000,
            ci_width_target=0.005
        )
        
        observed_rate = result['observed_rate']
        alpha = 0.05
        
        # The observed rate should be within the CI of the true alpha
        assert result['ci_lower'] <= alpha <= result['ci_upper'], \
            f"True alpha {alpha} should be within CI [{result['ci_lower']}, {result['ci_upper']}]"
        
        # The observed rate should be reasonably close to alpha
        assert abs(observed_rate - alpha) < 0.02, \
            f"Observed rate {observed_rate} should be close to alpha {alpha}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])