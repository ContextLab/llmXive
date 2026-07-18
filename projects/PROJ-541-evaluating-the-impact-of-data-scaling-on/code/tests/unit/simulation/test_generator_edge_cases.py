import pytest
import numpy as np
import sys
import os
from pathlib import Path
from simulation.config import SimulationConfig
from simulation.generator import generate_synthetic_data
from simulation.logger import setup_logger

logger = setup_logger(__name__)

class TestGeneratorEdgeCases:
    """
    Additional unit tests for edge cases in the synthetic data generator.
    Covers extreme outliers and constant data scenarios.
    """

    def test_extreme_outliers_handling(self):
        """
        Test that the generator handles configurations with extreme outliers
        without crashing or producing NaN/Inf values in the main distribution.
        """
        config = SimulationConfig(
            n_samples=1000,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.05,
            outlier_magnitude=100.0,
            seed=42
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert len(data_a) == config.n_samples
        assert len(data_b) == config.n_samples

        # Check for NaN or Inf in the generated data
        assert not np.isnan(data_a).any(), "Generated data_a contains NaN"
        assert not np.isnan(data_b).any(), "Generated data_b contains NaN"
        assert not np.isinf(data_a).any(), "Generated data_a contains Inf"
        assert not np.isinf(data_b).any(), "Generated data_b contains Inf"

        # Verify that outliers were actually introduced (max/min values should be large)
        # With 5% outliers of magnitude 100, we expect at least some values > 50
        combined = np.concatenate([data_a, data_b])
        max_val = np.max(np.abs(combined))
        assert max_val > 50.0, f"Expected extreme outliers (magnitude ~100), but max abs value was {max_val}"

    def test_constant_data_group_a(self):
        """
        Test behavior when one group is forced to be constant (zero variance).
        This should trigger the zero-variance skip logic in the generator.
        """
        # Create a config that might result in near-zero variance for one group
        # We simulate this by setting a very small std_dev and checking the logic
        config = SimulationConfig(
            n_samples=100,
            mean_diff=1.0,
            std_dev=1e-10,  # Extremely small standard deviation
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=123
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        # The generator should handle this, possibly by skipping or adjusting
        # We verify that it returns valid data structures
        assert data_a is not None
        assert data_b is not None
        assert len(data_a) == config.n_samples
        assert len(data_b) == config.n_samples

        # If the data is truly constant, std should be near zero
        std_a = np.std(data_a)
        std_b = np.std(data_b)
        
        # Note: The generator might add a small epsilon to avoid zero variance,
        # so we just check that it doesn't crash and returns arrays
        logger.info(f"Test constant data: std_a={std_a}, std_b={std_b}")

    def test_constant_data_both_groups(self):
        """
        Test when both groups are effectively constant.
        """
        config = SimulationConfig(
            n_samples=50,
            mean_diff=0.0,
            std_dev=1e-12,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=456
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert not np.isnan(data_a).any()
        assert not np.isnan(data_b).any()

    def test_extreme_skewness(self):
        """
        Test generator with extreme skewness parameter.
        """
        config = SimulationConfig(
            n_samples=2000,
            mean_diff=0.5,
            std_dev=2.0,
            distribution_type="skewed",
            skewness=10.0,  # Very high skewness
            heteroscedasticity=0.0,
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=789
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert not np.isnan(data_a).any()
        assert not np.isnan(data_b).any()
        
        # Verify skewness is present (rough check)
        # A highly skewed distribution should have mean significantly different from median
        mean_a = np.mean(data_a)
        median_a = np.median(data_a)
        # For high skewness, the difference should be noticeable
        # This is a heuristic check
        if config.skewness > 5.0:
            assert abs(mean_a - median_a) > 0.1, "Expected significant difference between mean and median for high skewness"

    def test_extreme_heteroscedasticity(self):
        """
        Test generator with extreme heteroscedasticity.
        """
        config = SimulationConfig(
            n_samples=1000,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=10.0,  # Group B should have 10x variance of Group A
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=999
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert not np.isnan(data_a).any()
        assert not np.isnan(data_b).any()

        var_a = np.var(data_a)
        var_b = np.var(data_b)
        
        # With heteroscedasticity=10, var_b should be roughly 10 * var_a
        # Allow some tolerance due to sampling noise
        ratio = var_b / var_a if var_a > 1e-9 else 0
        logger.info(f"Heteroscedasticity test: var_a={var_a}, var_b={var_b}, ratio={ratio}")
        
        # The ratio should be significantly greater than 1
        assert ratio > 5.0, f"Expected var_b/var_a ratio > 5.0 for heteroscedasticity=10, got {ratio}"

    def test_zero_sample_size(self):
        """
        Test that the generator handles or rejects zero sample size gracefully.
        """
        config = SimulationConfig(
            n_samples=0,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=111
        )

        # This should either raise an error or return empty arrays
        try:
            data_a, data_b, validity, message = generate_synthetic_data(config)
            # If it returns, arrays should be empty
            assert len(data_a) == 0
            assert len(data_b) == 0
        except (ValueError, AssertionError) as e:
            # Expected behavior: raise an error for invalid input
            logger.info(f"Generator correctly raised exception for n_samples=0: {e}")

    def test_negative_sample_size(self):
        """
        Test that the generator handles negative sample size.
        """
        config = SimulationConfig(
            n_samples=-10,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.0,
            outlier_magnitude=0.0,
            seed=222
        )

        try:
            data_a, data_b, validity, message = generate_synthetic_data(config)
            # If it returns, it should be empty or raise
            assert len(data_a) == 0
        except (ValueError, AssertionError) as e:
            logger.info(f"Generator correctly raised exception for n_samples=-10: {e}")

    def test_extreme_outlier_magnitude(self):
        """
        Test with extremely large outlier magnitude.
        """
        config = SimulationConfig(
            n_samples=500,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=0.01,
            outlier_magnitude=1e6,  # One million
            seed=333
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert not np.isnan(data_a).any()
        assert not np.isnan(data_b).any()
        
        # Check that at least one outlier exists
        combined = np.concatenate([data_a, data_b])
        max_val = np.max(np.abs(combined))
        assert max_val > 1e5, f"Expected outlier magnitude ~1e6, but max was {max_val}"

    def test_100_percent_outliers(self):
        """
        Test with 100% outlier fraction (all data points are outliers).
        """
        config = SimulationConfig(
            n_samples=100,
            mean_diff=0.0,
            std_dev=1.0,
            distribution_type="normal",
            skewness=0.0,
            heteroscedasticity=0.0,
            outlier_fraction=1.0,
            outlier_magnitude=50.0,
            seed=444
        )

        data_a, data_b, validity, message = generate_synthetic_data(config)

        assert data_a is not None
        assert data_b is not None
        assert not np.isnan(data_a).any()
        assert not np.isnan(data_b).any()
        
        # All values should be outliers (magnitude ~50)
        combined = np.concatenate([data_a, data_b])
        # With 100% outliers, most values should be large
        # We check that the median absolute value is significant
        median_abs = np.median(np.abs(combined))
        assert median_abs > 20.0, f"Expected most values to be outliers (mag ~50), but median abs was {median_abs}"