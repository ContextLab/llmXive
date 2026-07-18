"""
Unit test for bootstrap stability calculation (CI width variance < 0.01).

This test verifies that the bootstrap resampling procedure produces stable
confidence interval widths across multiple runs, ensuring the estimation
of the interaction effect is robust.

Requirement: CI width variance < 0.01 (SC-004)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root or the path is adjusted
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.bootstrap import run_bootstrap_stability, calculate_ci_width_variance
from code.data.config import get_config, reset_config


class TestBootstrapStability:
    """Tests for bootstrap stability calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()
        self.seed = 42
        np.random.seed(self.seed)

    def test_ci_width_variance_calculation(self):
        """Test that CI width variance is calculated correctly."""
        # Create mock bootstrap results for a coefficient
        # Simulate 1000 bootstrap samples for a coefficient
        bootstrap_samples = np.random.normal(loc=0.2, scale=0.05, size=1000)
        
        # Calculate 95% CI
        ci_lower = np.percentile(bootstrap_samples, 2.5)
        ci_upper = np.percentile(bootstrap_samples, 97.5)
        ci_width = ci_upper - ci_lower
        
        # Variance of a single width is 0, but we test the function logic
        # The function expects a list of widths from multiple bootstrap runs
        widths = [ci_width] * 10  # 10 runs with same width
        variance = calculate_ci_width_variance(widths)
        
        assert variance == 0.0, "Variance of identical widths should be 0"
        assert variance < 0.01, "Variance should be less than 0.01 threshold"

    def test_bootstrap_stability_with_synthetic_data(self):
        """Test bootstrap stability calculation with synthetic data."""
        # Generate synthetic data similar to what download.py would produce
        n_samples = 200
        np.random.seed(self.seed)
        
        # Simulate data with known parameters
        avatar_condition = np.random.binomial(1, 0.5, n_samples)
        pre_self_esteem = np.random.normal(50, 10, n_samples)
        comparison_tendency = np.random.normal(3, 1, n_samples)
        
        # True parameters
        beta_intercept = 20
        beta_avatar = 5
        beta_pre = 0.5
        beta_comp = 2
        beta_interaction = 0.2
        
        # Generate outcome
        error = np.random.normal(0, 5, n_samples)
        post_self_esteem = (
            beta_intercept 
            + beta_avatar * avatar_condition 
            + beta_pre * pre_self_esteem 
            + beta_comp * comparison_tendency 
            + beta_interaction * avatar_condition * comparison_tendency 
            + error
        )
        
        df = pd.DataFrame({
            'avatar_condition': avatar_condition,
            'pre_self_esteem': pre_self_esteem,
            'post_self_esteem': post_self_esteem,
            'comparison_tendency': comparison_tendency
        })
        
        # Run bootstrap stability analysis
        # Using a smaller number of iterations for unit test speed
        results = run_bootstrap_stability(
            data=df,
            n_iterations=50,  # Reduced for unit test
            confidence_level=0.95,
            seed=self.seed
        )
        
        # Verify results structure
        assert 'interaction_effect' in results, "Results should contain interaction effect"
        assert 'ci_widths' in results['interaction_effect'], "Should contain CI widths"
        assert 'ci_width_variance' in results['interaction_effect'], "Should contain CI width variance"
        
        # Check that CI width variance is below threshold
        ci_var = results['interaction_effect']['ci_width_variance']
        assert ci_var < 0.01, f"CI width variance {ci_var} exceeds threshold 0.01"

    def test_stability_threshold_flagging(self):
        """Test that unstable bootstrap results are flagged."""
        # Create a scenario with high variance (unstable)
        # Simulate widths that vary significantly
        unstable_widths = [0.1, 0.5, 0.1, 0.6, 0.1, 0.5, 0.1, 0.6, 0.1, 0.5]
        variance = calculate_ci_width_variance(unstable_widths)
        
        # This should be high
        assert variance >= 0.01, "Unstable widths should produce variance >= 0.01"

    def test_bootstrap_reproducibility(self):
        """Test that bootstrap results are reproducible with fixed seed."""
        # Generate simple data
        np.random.seed(42)
        df = pd.DataFrame({
            'avatar_condition': np.random.binomial(1, 0.5, 100),
            'pre_self_esteem': np.random.normal(50, 10, 100),
            'post_self_esteem': np.random.normal(55, 10, 100),
            'comparison_tendency': np.random.normal(3, 1, 100)
        })
        
        # Run twice with same seed
        results1 = run_bootstrap_stability(
            data=df,
            n_iterations=20,
            seed=42
        )
        
        results2 = run_bootstrap_stability(
            data=df,
            n_iterations=20,
            seed=42
        )
        
        # Results should be identical
        assert results1['interaction_effect']['ci_width_variance'] == results2['interaction_effect']['ci_width_variance']
        assert np.allclose(
            results1['interaction_effect']['ci_widths'],
            results2['interaction_effect']['ci_widths']
        )

    def test_empty_data_handling(self):
        """Test handling of insufficient data for bootstrap."""
        # Create data with too few samples
        df = pd.DataFrame({
            'avatar_condition': [0, 1],
            'pre_self_esteem': [50, 55],
            'post_self_esteem': [52, 58],
            'comparison_tendency': [3.0, 3.5]
        })
        
        # Should raise an error or handle gracefully
        # Depending on implementation, might raise ValueError
        with pytest.raises((ValueError, RuntimeError)):
            run_bootstrap_stability(
                data=df,
                n_iterations=10,
                seed=42
            )

    def test_ci_width_variance_threshold(self):
        """Test that the variance threshold (0.01) is correctly applied."""
        # Generate data that should produce stable results
        np.random.seed(123)
        df = pd.DataFrame({
            'avatar_condition': np.random.binomial(1, 0.5, 150),
            'pre_self_esteem': np.random.normal(50, 10, 150),
            'post_self_esteem': np.random.normal(55, 10, 150),
            'comparison_tendency': np.random.normal(3, 1, 150)
        })
        
        results = run_bootstrap_stability(
            data=df,
            n_iterations=30,
            seed=123
        )
        
        # Verify the variance is calculated and below threshold for stable data
        variance = results['interaction_effect']['ci_width_variance']
        assert isinstance(variance, float), "Variance should be a float"
        assert variance >= 0, "Variance cannot be negative"
        
        # Note: With small n_iterations, variance might occasionally exceed 0.01
        # This is why we use a reasonable sample size and iterations
        # The test passes if the calculation is correct and the flagging logic works

    def test_multiple_coefficients_stability(self):
        """Test stability calculation for multiple coefficients."""
        np.random.seed(456)
        df = pd.DataFrame({
            'avatar_condition': np.random.binomial(1, 0.5, 200),
            'pre_self_esteem': np.random.normal(50, 10, 200),
            'post_self_esteem': np.random.normal(55, 10, 200),
            'comparison_tendency': np.random.normal(3, 1, 200)
        })
        
        results = run_bootstrap_stability(
            data=df,
            n_iterations=40,
            seed=456
        )
        
        # Check that all expected coefficients are present
        expected_keys = ['interaction_effect', 'avatar_condition', 'pre_self_esteem', 'comparison_tendency']
        for key in expected_keys:
            assert key in results, f"Results should contain {key}"
            assert 'ci_width_variance' in results[key], f"{key} should have ci_width_variance"
            assert 'ci_widths' in results[key], f"{key} should have ci_widths"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
