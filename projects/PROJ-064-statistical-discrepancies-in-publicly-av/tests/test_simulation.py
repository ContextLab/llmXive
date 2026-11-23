"""
Unit tests for Anderson-Darling and Kolmogorov-Smirnov test outputs.

This module verifies that the statistical tests implemented in code/analysis.py
and code/simulation.py produce expected results when fed known distributions.

It specifically tests:
1. Anderson-Darling test against a known Negative Binomial distribution.
2. Kolmogorov-Smirnov test against a known Uniform distribution.
3. Robustness of the tests against edge cases (empty data, single value).
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis import anderson_darling_test, kolmogorov_smirnov_test, load_null_distribution
from simulation import fit_negative_binomial, generate_nb_null_model

# Fix random seed for reproducibility in tests
TEST_SEED = 42
np.random.seed(TEST_SEED)


class TestAndersonDarling:
    """Tests for the Anderson-Darling test implementation."""

    def test_ad_test_known_distribution(self):
        """
        Test AD test against a known Negative Binomial distribution.
        
        When the observed data is drawn from the same distribution as the
        null hypothesis, the p-value should be high (fail to reject).
        """
        # Generate a known Negative Binomial distribution
        # Parameters: n=10, p=0.5
        n, p = 10, 0.5
        true_dist = stats.nbinom(n, p)
        observed_data = true_dist.rvs(size=1000, random_state=TEST_SEED)

        # Create a mock null distribution (also NB with same params)
        null_dist = true_dist.rvs(size=10000, random_state=TEST_SEED + 1)

        # Run the test
        result = anderson_darling_test(observed_data, null_dist)

        # Verify output structure
        assert "statistic" in result, "Result missing 'statistic' key"
        assert "p_value" in result, "Result missing 'p_value' key"
        assert "critical_values" in result, "Result missing 'critical_values' key"

        # Since data comes from the same distribution, p-value should be > 0.05
        # (allowing some tolerance for randomness)
        assert result["p_value"] > 0.01, f"Expected high p-value for matching distributions, got {result['p_value']}"

    def test_ad_test_different_distribution(self):
        """
        Test AD test against a clearly different distribution.
        
        When observed data is Normal but null is NB, we expect to reject.
        """
        # Observed: Normal distribution
        observed_data = np.random.normal(loc=0, scale=1, size=1000)

        # Null: Negative Binomial (discrete, skewed)
        null_data = stats.nbinom.rvs(n=10, p=0.5, size=10000)

        result = anderson_darling_test(observed_data, null_data)

        # Should detect the difference
        assert result["p_value"] < 0.05, f"Expected low p-value for different distributions, got {result['p_value']}"

    def test_ad_test_edge_cases(self):
        """Test AD test with edge cases."""
        # Single value
        with pytest.raises(Exception):
            anderson_darling_test([1], [1, 2, 3, 4, 5])

        # Empty array
        with pytest.raises(Exception):
            anderson_darling_test([], [1, 2, 3])


class TestKolmogorovSmirnov:
    """Tests for the Kolmogorov-Smirnov test implementation."""

    def test_ks_test_uniform(self):
        """
        Test KS test against a known Uniform distribution.
        
        When observed data is Uniform(0,1) and null is Uniform(0,1),
        p-value should be high.
        """
        observed = np.random.uniform(0, 1, size=1000)
        null = np.random.uniform(0, 1, size=10000)

        result = kolmogorov_smirnov_test(observed, null)

        assert "statistic" in result
        assert "p_value" in result

        # High p-value expected
        assert result["p_value"] > 0.01

    def test_ks_test_different_distributions(self):
        """
        Test KS test with clearly different distributions.
        """
        observed = np.random.exponential(scale=1.0, size=1000)
        null = np.random.normal(loc=0, scale=1, size=10000)

        result = kolmogorov_smirnov_test(observed, null)

        # Should reject null
        assert result["p_value"] < 0.05

    def test_ks_test_with_dataframe_input(self):
        """
        Test KS test handles DataFrame input correctly.
        
        This verifies the integration with the project's data model.
        """
        # Create a mock DataFrame with a 'discrepancy_abs' column
        df = pd.DataFrame({
            'discrepancy_abs': np.random.normal(0, 1, 1000)
        })

        # Create a mock null distribution
        null = np.random.normal(0, 1, 10000)

        # The function should extract the column if a DataFrame is passed
        # or handle the Series/DataFrame appropriately
        result = kolmogorov_smirnov_test(df['discrepancy_abs'], null)

        assert result["p_value"] is not None


class TestIntegrationWithSimulation:
    """Integration tests combining simulation and analysis."""

    def test_full_nb_pipeline(self):
        """
        Test the full pipeline: Fit NB -> Generate Null -> Test Observed.
        """
        # 1. Generate synthetic data from NB
        true_n, true_p = 5, 0.3
        true_dist = stats.nbinom(true_n, true_p)
        observed = true_dist.rvs(2000, random_state=TEST_SEED)

        # 2. Fit NB to observed (using robust stats as per T055)
        # We pass the raw data; the function should handle estimation
        params = fit_negative_binomial(observed)

        assert "mu" in params or "n" in params, "Fit failed to return parameters"

        # 3. Generate null model using fitted params
        null_samples = generate_nb_null_model(params, size=10000)

        # 4. Run AD test
        ad_result = anderson_darling_test(observed, null_samples)

        # 5. Run KS test
        ks_result = kolmogorov_smirnov_test(observed, null_samples)

        # Both should fail to reject (high p-values)
        assert ad_result["p_value"] > 0.05, f"AD test rejected matching distribution: {ad_result['p_value']}"
        assert ks_result["p_value"] > 0.05, f"KS test rejected matching distribution: {ks_result['p_value']}"

    def test_mismatched_pipeline(self):
        """
        Test pipeline where observed data does NOT match the fitted null.
        """
        # Observed: Exponential
        observed = np.random.exponential(scale=1.0, size=2000)

        # Fit NB to it (will be a poor fit)
        params = fit_negative_binomial(observed)
        null_samples = generate_nb_null_model(params, size=10000)

        # Run tests
        ad_result = anderson_darling_test(observed, null_samples)
        ks_result = kolmogorov_smirnov_test(observed, null_samples)

        # Should reject
        assert ad_result["p_value"] < 0.05, "AD test failed to detect mismatch"
        assert ks_result["p_value"] < 0.05, "KS test failed to detect mismatch"


class TestArtifactGeneration:
    """Tests ensuring tests produce required artifacts if applicable."""

    def test_output_format_compliance(self):
        """
        Verify that test results match the expected schema for downstream consumption.
        """
        observed = np.random.normal(0, 1, 100)
        null = np.random.normal(0, 1, 1000)

        ad_res = anderson_darling_test(observed, null)
        ks_res = kolmogorov_smirnov_test(observed, null)

        # Check required keys
        for res in [ad_res, ks_res]:
            assert isinstance(res, dict)
            assert "statistic" in res
            assert "p_value" in res
            assert isinstance(res["statistic"], (int, float, np.number))
            assert isinstance(res["p_value"], (int, float, np.number))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])