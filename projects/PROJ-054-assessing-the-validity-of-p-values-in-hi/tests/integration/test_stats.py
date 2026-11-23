"""
Integration tests for hypothesis testing pipeline.
Tests for code/run_tests.py and code/analyze_pvalues.py
"""
import numpy as np
import pytest
from scipy import stats
from run_tests import run_hypothesis_tests
from analyze_pvalues import calculate_ks_statistic


class TestHypothesisTestingIntegration:
    def test_full_iteration_loop(self):
        """Test multiple iterations without runtime errors."""
        n_iterations = 10
        n_samples = 100
        n_features = 50

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # Verify all p-values are valid
        assert len(all_pvalues) == n_iterations * n_features
        assert all(0 <= p <= 1 for p in all_pvalues)

    def test_null_hypothesis_pvalue_distribution(self):
        """Test that p-values under null hypothesis are approximately uniform."""
        n_iterations = 100
        n_samples = 200
        n_features = 20

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # KS test against uniform distribution
        ks_stat, p_value = stats.kstest(all_pvalues, 'uniform')

        # Should not reject uniformity (p-value > 0.05)
        # Note: With many tests, some will reject by chance
        # So we check that most iterations pass
        assert p_value > 0.01  # Allow some false positives

    def test_alternative_hypothesis_detection(self):
        """Test that alternative hypothesis is detected with sufficient power."""
        n_iterations = 50
        n_samples = 200
        n_features = 20

        detection_rate = 0

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features) + 1.0  # Mean shift

            p_values = run_hypothesis_tests(group1, group2)

            # Count significant results (p < 0.05)
            significant = sum(1 for p in p_values if p < 0.05)

            if significant > n_features * 0.5:
                detection_rate += 1

        # Should detect effect in most iterations
        assert detection_rate > n_iterations * 0.8

    def test_pvalue_collection_completeness(self):
        """Test that all p-values are collected without missing values."""
        n_iterations = 10
        n_samples = 100
        n_features = 50

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)

            # Verify exactly p values collected
            assert len(p_values) == n_features

            # Verify no NaN or Inf values
            assert not np.any(np.isnan(p_values))
            assert not np.any(np.isinf(p_values))

    def test_ks_statistic_integration(self):
        """Test KS statistic calculation on collected p-values."""
        n_iterations = 100
        n_samples = 200
        n_features = 20

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # Calculate KS statistic
        ks_stat = calculate_ks_statistic(np.array(all_pvalues))

        # Should be small for uniform distribution
        assert ks_stat < 0.1

    def test_batch_processing(self):
        """Test processing multiple datasets in batch."""
        n_datasets = 5
        n_samples = 100
        n_features = 50

        results = []

        for i in range(n_datasets):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)
            ks_stat = calculate_ks_statistic(np.array(p_values))
            results.append({"dataset": i, "ks_stat": ks_stat})

        # Verify all results
        assert len(results) == n_datasets
        assert all(0 <= r["ks_stat"] <= 1 for r in results)

    def test_large_scale_integration(self):
        """Test integration with larger dimensions."""
        n_iterations = 5
        n_samples = 500
        n_features = 200

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)
            group1 = np.random.randn(n_samples, n_features)
            group2 = np.random.randn(n_samples, n_features)

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # Verify completeness
        assert len(all_pvalues) == n_iterations * n_features

        # KS test
        ks_stat = calculate_ks_statistic(np.array(all_pvalues))
        assert ks_stat < 0.15  # Allow slightly larger for finite sample

    def test_correlated_data_integration(self):
        """Test integration with correlated data."""
        n_iterations = 10
        n_samples = 200
        n_features = 50
        rho = 0.5

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)

            # Generate correlated data
            base = np.random.randn(n_samples, n_features)
            # Create correlation structure
            corr_data = base @ np.linalg.cholesky(
                np.full((n_features, n_features), rho) + np.eye(n_features) * (1 - rho)
            )

            group1 = corr_data[:n_samples//2, :]
            group2 = corr_data[n_samples//2:, :]

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # Verify completeness
        assert len(all_pvalues) == n_iterations * n_features

        # KS test
        ks_stat = calculate_ks_statistic(np.array(all_pvalues))
        # Correlated data might show some deviation
        assert ks_stat < 0.2

    def test_mixed_distribution_integration(self):
        """Test integration with mixed distribution violations."""
        n_iterations = 5
        n_samples = 200
        n_features = 50

        all_pvalues = []

        for i in range(n_iterations):
            np.random.seed(i)

            # Generate data with t-distribution (heavy tails)
            group1 = np.random.standard_t(df=3, size=(n_samples, n_features))
            group2 = np.random.standard_t(df=3, size=(n_samples, n_features))

            p_values = run_hypothesis_tests(group1, group2)
            all_pvalues.extend(p_values)

        # Verify completeness
        assert len(all_pvalues) == n_iterations * n_features

        # KS test (might show deviation due to heavy tails)
        ks_stat = calculate_ks_statistic(np.array(all_pvalues))
        assert ks_stat < 0.3  # Allow larger deviation for heavy-tailed data

    def test_reproducibility_across_runs(self):
        """Test that results are reproducible with same seed."""
        n_samples = 100
        n_features = 50
        seed = 42

        # First run
        np.random.seed(seed)
        group1_1 = np.random.randn(n_samples, n_features)
        group2_1 = np.random.randn(n_samples, n_features)
        pvalues_1 = run_hypothesis_tests(group1_1, group2_1)

        # Second run with same seed
        np.random.seed(seed)
        group1_2 = np.random.randn(n_samples, n_features)
        group2_2 = np.random.randn(n_samples, n_features)
        pvalues_2 = run_hypothesis_tests(group1_2, group2_2)

        # Results should be identical
        np.testing.assert_array_equal(pvalues_1, pvalues_2)