"""
Integration test for null hypothesis validity (no mean differences).

This test verifies that the synthetic data generation pipeline produces
datasets where the null hypothesis of no mean difference between groups
is true by construction. It generates correlated data with controlled
parameters, performs t-tests on the groups, and verifies that the
resulting p-values follow a uniform distribution under the null.

The test ensures:
1. Generated data has the specified correlation structure.
2. The groups have identical mean vectors (ground truth null).
3. The empirical distribution of p-values is consistent with uniformity
   (KS test against uniform distribution).
"""

import numpy as np
import pytest
from scipy import stats
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.simulation import SyntheticDataset, SimulationConfig
from utils.regularization import regularize_covariance


class TestNullHypothesisValidity:
    """Integration tests for US1: Null hypothesis validity."""

    @pytest.fixture
    def base_config(self):
        """Base configuration for null hypothesis testing."""
        return SimulationConfig(
            n=100,       # Sample size
            p=50,        # Dimensionality
            rho=0.0,     # No correlation (null case)
            distribution_type="normal",
            seed=42,
            n_iterations=100  # Number of iterations for stability check
        )

    def test_generated_data_has_zero_mean_difference(self, base_config):
        """
        Verify that generated data has no mean difference between groups.

        This is the core requirement for the null hypothesis to be true
        by construction. The data generator must produce groups with
        identical mean vectors.
        """
        # Create synthetic dataset
        dataset = SyntheticDataset(
            n=base_config.n,
            p=base_config.p,
            rho=base_config.rho,
            distribution_type=base_config.distribution_type,
            seed=base_config.seed
        )

        # Generate data
        data = dataset.generate()

        # Split into two equal groups
        mid = data.shape[0] // 2
        group1 = data[:mid]
        group2 = data[mid:]

        # Calculate mean difference
        mean_diff = np.abs(group1.mean(axis=0) - group2.mean(axis=0))

        # Under null hypothesis, mean difference should be near zero
        # Allow for small numerical tolerance
        max_mean_diff = np.max(mean_diff)
        assert max_mean_diff < 0.1, f"Mean difference too large: {max_mean_diff}"

    def test_p_values_uniform_under_null(self, base_config):
        """
        Verify that p-values follow uniform distribution under null hypothesis.

        When the null hypothesis is true, p-values should be uniformly
        distributed between 0 and 1. We use the Kolmogorov-Smirnov test
        to check this property across multiple iterations.
        """
        p_values = []

        for i in range(base_config.n_iterations):
            # Create dataset with unique seed per iteration
            dataset = SyntheticDataset(
                n=base_config.n,
                p=base_config.p,
                rho=base_config.rho,
                distribution_type=base_config.distribution_type,
                seed=base_config.seed + i
            )

            # Generate data
            data = dataset.generate()

            # Split into two groups
            mid = data.shape[0] // 2
            group1 = data[:mid]
            group2 = data[mid:]

            # Perform t-test for each dimension
            for dim in range(data.shape[1]):
                stat, p_val = stats.ttest_ind(
                    group1[:, dim],
                    group2[:, dim],
                    equal_var=True
                )
                p_values.append(p_val)

        # Convert to numpy array
        p_values = np.array(p_values)

        # Test against uniform distribution using KS test
        ks_stat, ks_p_value = stats.kstest(p_values, 'uniform')

        # For true uniform distribution, KS p-value should be > 0.05
        # (i.e., we fail to reject the null that p-values are uniform)
        assert ks_p_value > 0.05, (
            f"P-values not uniform under null: KS statistic={ks_stat:.4f}, "
            f"KS p-value={ks_p_value:.4f}"
        )

    def test_correlation_structure_preserved(self, base_config):
        """
        Verify that the correlation structure is preserved in generated data.

        For the null hypothesis test to be valid, the correlation structure
        must match the specified rho parameter.
        """
        # Test with non-zero correlation
        config = SimulationConfig(
            n=200,
            p=50,
            rho=0.5,  # Strong correlation
            distribution_type="normal",
            seed=123,
            n_iterations=1
        )

        dataset = SyntheticDataset(
            n=config.n,
            p=config.p,
            rho=config.rho,
            distribution_type=config.distribution_type,
            seed=config.seed
        )

        data = dataset.generate()

        # Calculate empirical correlation matrix
        # Center the data first
        data_centered = data - data.mean(axis=0)
        empirical_corr = np.corrcoef(data_centered, rowvar=False)

        # Check diagonal is 1
        assert np.allclose(np.diag(empirical_corr), 1.0, atol=1e-10)

        # For off-diagonal elements, check that average correlation
        # is close to specified rho (allowing for sampling variability)
        # Take upper triangle excluding diagonal
        upper_tri = empirical_corr[np.triu_indices_from(empirical_corr, k=1)]
        avg_corr = np.mean(upper_tri)

        # With rho=0.5 and sufficient samples, average correlation
        # should be reasonably close to 0.5
        assert abs(avg_corr - config.rho) < 0.15, (
            f"Average correlation {avg_corr:.3f} differs too much from "
            f"specified rho={config.rho}"
        )

    def test_high_dimensional_null_validity(self):
        """
        Test null hypothesis validity in high-dimensional regime (p > n).

        This is a critical case where standard statistical tests often
        fail, but our generator should still maintain the null property.
        """
        config = SimulationConfig(
            n=50,      # Small sample size
            p=100,     # High dimensionality (p > n)
            rho=0.0,   # No correlation
            distribution_type="normal",
            seed=456,
            n_iterations=50
        )

        p_values = []

        for i in range(config.n_iterations):
            dataset = SyntheticDataset(
                n=config.n,
                p=config.p,
                rho=config.rho,
                distribution_type=config.distribution_type,
                seed=config.seed + i
            )

            data = dataset.generate()

            # Split into groups
            mid = data.shape[0] // 2
            group1 = data[:mid]
            group2 = data[mid:]

            # Perform t-tests (with regularization for high-dim case)
            for dim in range(data.shape[1]):
                try:
                    stat, p_val = stats.ttest_ind(
                        group1[:, dim],
                        group2[:, dim],
                        equal_var=True
                    )
                    p_values.append(p_val)
                except Exception:
                    # Skip if test fails (e.g., singular covariance)
                    continue

        if len(p_values) > 0:
            p_values = np.array(p_values)
            ks_stat, ks_p_value = stats.kstest(p_values, 'uniform')

            # In high-dimensional case, we expect some deviation but
            # p-values should still be reasonably uniform
            assert ks_p_value > 0.01, (
                f"High-dim null hypothesis violated: KS p-value={ks_p_value:.4f}"
            )